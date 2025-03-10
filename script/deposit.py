from script.set_up_script import setup_script
from moccasin.config import get_active_network
import boa
from boa.contracts.abi.abi_contract import ABIContract

"""
使用到的函数：
function supply(
    address asset,
    uint256 amount,
    address onBehalfOf,
    uint16 referralCode
) public virtual override


function getUserAccountData(address user) external view virtual override returns (
    uint256 totalCollateralBase,
    uint256 totalDebtBase,
    uint256 availableBorrowsBase,
    uint256 currentLiquidationThreshold,
    uint256 ltv,
    uint256 healthFactor
)
"""


def deposit(usdc, weth) -> ABIContract:
    print("----------------------------------------------------------")
    print("Starting deposit script...")
    my_address = boa.env.eoa
    network_config = get_active_network()
    aave_PoolAddressesProvider = network_config.manifest_named(
        "aave_PoolAddressesProvider"
    )
    pool_address = aave_PoolAddressesProvider.getPool()

    # 确保我们使用正确的池合约
    pool_contract = network_config.manifest_named("aave_Pool", address=pool_address)

    # 处理USDC (USDC是6位小数的代币)
    usdc_balanceOf = usdc.balanceOf(my_address)
    print(f"USDC余额: {usdc_balanceOf}")

    if usdc_balanceOf > 0:
        # 检查当前授权额度
        allowed_usdc_amount = usdc.allowance(my_address, pool_contract.address)
        print(f"当前USDC授权额度: {allowed_usdc_amount}")

        # 如果授权额度不足，则增加授权
        if allowed_usdc_amount < usdc_balanceOf:
            print(f"增加USDC授权额度到: {usdc_balanceOf}")
            usdc.approve(pool_contract.address, usdc_balanceOf)

        # 尝试存款
        try:
            pool_contract.supply(usdc.address, usdc_balanceOf, my_address, 0)
            print("USDC供应成功")
        except Exception as e:
            print(f"USDC供应失败: {e}")

    # WETH处理部分类似
    weth_balanceOf = weth.balanceOf(my_address)
    print(f"WETH余额: {weth_balanceOf}")

    if weth_balanceOf > 0:
        allowed_weth_amount = weth.allowance(my_address, pool_contract.address)
        print(f"当前WETH授权额度: {allowed_weth_amount}")

        if allowed_weth_amount < weth_balanceOf:
            print(f"增加WETH授权额度到: {weth_balanceOf}")
            weth.approve(pool_contract.address, weth_balanceOf)

        try:
            pool_contract.supply(weth.address, weth_balanceOf, my_address, 0)
            print("WETH供应成功")
        except Exception as e:
            print(f"WETH供应失败: {e}")

    print("Deposit script complete!")

    try:
        (
            totalCollateralBase,
            totalDebtBase,
            availableBorrowsBase,
            currentLiquidationThreshold,
            ltv,
            healthFactor,
        ) = pool_contract.getUserAccountData(my_address)
        print("用户账户数据:")
        print(f"totalCollateralBase: {totalCollateralBase}")
        print(f"totalDebtBase: {totalDebtBase}")
        print(f"availableBorrowsBase: {availableBorrowsBase}")
        print(f"currentLiquidationThreshold: {currentLiquidationThreshold}")
        print(f"ltv: {ltv}")
        print(f"healthFactor: {healthFactor}")
    except Exception as e:
        print(f"获取用户账户数据失败: {e}")

    return pool_contract


def moccasin_main():
    usdc, weth, _, _ = setup_script()
    deposit(usdc, weth)
