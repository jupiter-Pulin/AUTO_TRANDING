from moccasin.config import get_active_network
from script.set_up_script import setup_script
from script.deposit import deposit
import boa


"""
目标：
1. 获取用户的 USDC 和 WETH 余额
2. 将其按照美元计价
3. 计算用户的总资产
4. 目标比例:40% USDC 和 60% WETH
5. 如果 USDC 比例超过 40% + 3% 或 WETH 比例低于 60% - 3%，提取超出的部分并通过 Uniswap 交换
"""


"""
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }
 function exactInputSingle(
    struct ISwapRouter.ExactInputSingleParams params
  ) external returns (uint256 amountOut)

"""
# 常量
SIX_DECIMALS = int(1e6)  # USDC 的精度
EIGHTEEN_DECIMALS = int(1e18)  # WETH 的精度
TARGET_THRESHOLD = {"usdc": 0.4, "weth": 0.6}  # 目标比例
BUFFER = 0.03  # 3% 缓冲区

my_address = boa.env.eoa


def check_balance(
    usdc, weth, a_usdc, a_weth, usdc_price_feed, eth_price_feed, pool_contract
):
    print("----------------------------------------------------------")
    print("Checking balance...")

    # 获取价值
    usdc_price_normalized, usdc_value = check_value(a_usdc, usdc_price_feed)
    weth_price_normalized, weth_value = check_value(a_weth, eth_price_feed)

    total_value = usdc_value + weth_value
    print(f"USDC 价值: {usdc_value} USD")
    print(f"WETH 价值: {weth_value} USD")
    print(f"总价值: {total_value} USD")

    # 计算当前比例
    current_usdc_ratio = usdc_value / total_value if total_value > 0 else 0
    current_weth_ratio = weth_value / total_value if total_value > 0 else 0
    print(f"当前 USDC 比例: {current_usdc_ratio:.2%}")
    print(f"当前 WETH 比例: {current_weth_ratio:.2%}")

    # 判断是否需要重新平衡
    needs_rebalance = (
        abs(current_usdc_ratio - TARGET_THRESHOLD["usdc"]) > BUFFER
        or abs(current_weth_ratio - TARGET_THRESHOLD["weth"]) > BUFFER
    )

    if needs_rebalance:
        print("阈值不正常! 需要进行调整")
        # 计算目标价值
        target_usdc_value = total_value * TARGET_THRESHOLD["usdc"]
        target_weth_value = total_value * TARGET_THRESHOLD["weth"]

        if current_usdc_ratio > TARGET_THRESHOLD["usdc"] + BUFFER:
            # USDC 过多，计算超出的部分
            excess_usdc_value = usdc_value - target_usdc_value
            # 转换回代币数量 (价值/价格 = 数量)
            excess_usdc_amount = int(
                (excess_usdc_value / usdc_price_normalized) * SIX_DECIMALS
            )
            print(f"需要提取 {excess_usdc_amount / SIX_DECIMALS} USDC")

            # 确保不提取超过持有量
            a_usdc_balance = a_usdc.balanceOf(my_address)
            if excess_usdc_amount > a_usdc_balance:
                excess_usdc_amount = a_usdc_balance
                print(f"调整提取量至余额上限: {excess_usdc_amount / SIX_DECIMALS} USDC")

            usdc_withdraw_amount = token_withdraw(
                usdc, excess_usdc_amount, pool_contract
            )
            amountOut = swap_token_to_token(usdc_withdraw_amount, usdc, weth)
            print("swap 成功 现在执行deposit")
            redeposit(amountOut, weth)

            # 更新比例
            _, new_usdc_value = check_value(a_usdc, usdc_price_feed)
            _, new_weth_value = check_value(a_weth, eth_price_feed)
            new_total = new_usdc_value + new_weth_value
            new_usdc_ratio = new_usdc_value / new_total if new_total > 0 else 0
            new_weth_ratio = new_weth_value / new_total if new_total > 0 else 0
            print(f"当前 USDC 比例: {new_usdc_ratio:.2%}")
            print(f"当前 WETH 比例: {new_weth_ratio:.2%}")

            return new_usdc_ratio, new_weth_ratio

        elif current_weth_ratio > TARGET_THRESHOLD["weth"] + BUFFER:
            # WETH 过多，计算超出的部分
            excess_weth_value = weth_value - target_weth_value
            # 转换回代币数量 (价值/价格 = 数量)
            excess_weth_amount = int(
                (excess_weth_value / weth_price_normalized) * EIGHTEEN_DECIMALS
            )
            print(f"需要提取 {excess_weth_amount / EIGHTEEN_DECIMALS} WETH")

            # 确保不提取超过持有量
            a_weth_balance = a_weth.balanceOf(my_address)
            if excess_weth_amount > a_weth_balance:
                excess_weth_amount = a_weth_balance
                print(
                    f"调整提取量至余额上限: {excess_weth_amount / EIGHTEEN_DECIMALS} WETH"
                )

            weth_withdraw_amount = token_withdraw(
                weth, excess_weth_amount, pool_contract
            )
            amountOut = swap_token_to_token(weth_withdraw_amount, weth, usdc)
            print("swap 成功 现在执行deposit")
            redeposit(amountOut, usdc)

            # 更新比例
            _, new_usdc_value = check_value(a_usdc, usdc_price_feed)
            _, new_weth_value = check_value(a_weth, eth_price_feed)
            new_total = new_usdc_value + new_weth_value
            new_usdc_ratio = new_usdc_value / new_total if new_total > 0 else 0
            new_weth_ratio = new_weth_value / new_total if new_total > 0 else 0
            print(f"当前 USDC 比例: {new_usdc_ratio:.2%}")
            print(f"当前 WETH 比例: {new_weth_ratio:.2%}")

            return new_usdc_ratio, new_weth_ratio

    return current_usdc_ratio, current_weth_ratio


def check_value(a_token, price_feed):
    print("Checking ratio...")
    a_token_balance = a_token.balanceOf(my_address)
    a_token_decimals = 10 ** a_token.decimals()  # 计算实际精度值
    a_token_normalized = a_token_balance / a_token_decimals

    a_token_price = price_feed.latestAnswer()
    a_token_decimals = 10 ** price_feed.decimals()
    a_token_price_normalized = a_token_price / a_token_decimals

    a_token_value = a_token_normalized * a_token_price_normalized

    return a_token_price_normalized, a_token_value


def token_withdraw(token, amount, pool_contract):
    print("----------------------------------------------------------")
    print("Starting withdraw script...")
    final_amount = pool_contract.withdraw(token.address, amount, my_address)
    return final_amount


def swap_token_to_token(amountIn, tokenIn, tokenOut) -> int:
    print("----------------------------------------------------------")
    print("Starting swap script...")

    active_network = get_active_network()
    uniswap_v3_router = active_network.manifest_named("uniswap_v3_router")
    token_allowance = tokenIn.allowance(my_address, uniswap_v3_router.address)
    if token_allowance < amountIn:
        tokenIn.approve(uniswap_v3_router.address, amountIn)
    minimum_amount_out = amountOutMinimum(tokenIn, tokenOut, amountIn)

    amountOut = uniswap_v3_router.exactInputSingle(
        (
            tokenIn.address,  # address
            tokenOut.address,  # address
            3000,  # uint24
            my_address,  # address
            amountIn,  # uint256
            minimum_amount_out,  # uint256
            0,  # uint160
        )
    )
    tokenIn_decimals = 10 ** tokenIn.decimals()
    tokenOut_decimals = 10 ** tokenOut.decimals()
    print(
        f"交换 {amountIn / tokenIn_decimals} {tokenIn.name()} 为 {amountOut / tokenOut_decimals} {tokenOut.name()}"
    )
    return amountOut


def amountOutMinimum(tokenIn, tokenOut, amountIn):
    active_network = get_active_network()
    uniswap_v3_quoter = active_network.manifest_named("uniswap_v3_quoter")

    # 调用Uniswap V3 Quoter合约的quoteExactInputSingle函数获取预期输出
    try:
        expected_amount_out = uniswap_v3_quoter.quoteExactInputSingle(
            tokenIn.address,  # 输入代币地址
            tokenOut.address,  # 输出代币地址
            3000,  # 费率，0.3%
            amountIn,  # 输入金额
            0,  # sqrtPriceLimitX96，设为0表示不限制价格
        )

        # 设置最小输出为预期输出的70%，提供滑点保护
        minimum_amount_out = int(expected_amount_out * 0.7)
        print(f"预期输出: {expected_amount_out}, 最小输出: {minimum_amount_out}")
        return minimum_amount_out

    except Exception as e:
        print(f"计算最小输出金额时出错: {e}")
        # 如果无法获取报价，提供一个非常低的最小值（以防万一）
        return 1


def redeposit(amount, token):
    print("----------------------------------------------------------")
    print("Starting redeposit script...")
    network_config = get_active_network()
    aave_PoolAddressesProvider = network_config.manifest_named(
        "aave_PoolAddressesProvider"
    )
    pool_address = aave_PoolAddressesProvider.getPool()

    # 确保我们使用正确的池合约
    pool_contract = network_config.manifest_named("aave_Pool", address=pool_address)
    token_balance = token.balanceOf(my_address)
    assert amount <= token_balance
    token.approve(pool_contract.address, amount)
    pool_contract.supply(token.address, amount, my_address, 0)
    print("redeposit 完成")


def run_rebalance():
    active_network = get_active_network()
    usdc_price_feed = active_network.manifest_named("usdc_price_feed")
    eth_price_feed = active_network.manifest_named("eth_price_feed")

    usdc, weth, a_usdc, a_weth = setup_script()
    pool_contract = deposit(usdc, weth)

    check_balance(
        usdc, weth, a_usdc, a_weth, usdc_price_feed, eth_price_feed, pool_contract
    )
    # print(f"调整后 USDC 余额: {a_usdc_balance / SIX_DECIMALS}")
    # print(f"调整后 WETH 余额: {a_weth_balance / EIGHTEEN_DECIMALS}")


def moccasin_main():
    run_rebalance()
