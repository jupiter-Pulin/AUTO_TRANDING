import boa
from moccasin.config import get_active_network

STARTING_WETH_BALANCE = int(1e18)
STARTING_BALANCE = int(1e21)
STARTING_USDC_BALANCE = int(1000e6)


def set_eth():
    print("Setting ETH...")
    boa.env.set_balance(boa.env.eoa, STARTING_BALANCE)
    print("ETH set!")


def add_eth_to_weth(weth):
    print("Adding ETH to WETH...")
    weth.deposit(value=STARTING_WETH_BALANCE)
    print("ending balance:", weth.balanceOf(boa.env.eoa))
    print("WETH SET!")


def add_eth_to_usdc(usdc):
    print("Adding ETH to USDC...")
    my_address = boa.env.eoa
    with boa.env.prank(usdc.owner()):
        usdc.updateMasterMinter(my_address)
    usdc.configureMinter(my_address, STARTING_USDC_BALANCE)
    usdc.mint(my_address, STARTING_USDC_BALANCE)
    print("USDC minted!")
    print("ending balance:", usdc.balanceOf(boa.env.eoa))


def setup_script():
    active_network = get_active_network()
    print("----------------------------------------------------------")
    print("Starting setup script...")
    usdc = active_network.manifest_named("usdc")
    weth = active_network.manifest_named("weth")
    aave_protocol_data_provider = active_network.manifest_named(
        "aave_protocol_data_provider"
    )

    if active_network.is_local_or_forked_network():
        set_eth()
        add_eth_to_weth(weth)
        add_eth_to_usdc(usdc)

        # aTokens_list = aave_protocol_data_provider.getAllATokens()
        # symbol = "aEth"
        # for a_token in aTokens_list:
        #     if a_token[0] == f"{symbol}USDC":
        #         a_usdc = active_network.manifest_named("a_usdc", address=a_token[1])
        #     elif a_token[0] == f"{symbol}WETH":
        #         a_weth = active_network.manifest_named("a_weth", address=a_token[1])

        # 直接获取对应的aToken地址
        a_usdc_address, _, _ = aave_protocol_data_provider.getReserveTokensAddresses(
            usdc.address
        )
        a_weth_address, _, _ = aave_protocol_data_provider.getReserveTokensAddresses(
            weth.address
        )
        # 实例化aToken合约
        a_usdc = active_network.manifest_named("usdc", address=a_usdc_address)
        a_weth = active_network.manifest_named("weth", address=a_weth_address)

    print("Setup script complete!")
    return usdc, weth, a_usdc, a_weth


def moccasin_main():
    setup_script()
