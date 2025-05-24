# AutoTrand: 自动资产再平衡系统（基于 Moccasin 框架）

AutoTrand 是一个基于 [Moccasin]框架开发的自动化资产再平衡脚本，集成了 Aave V3 和 Uniswap V3，实现资产的按比例自动配置和再投资。

---

## 🔧 功能说明

### 核心功能：

- 将用户的 USDC 与 WETH 存入 Aave 协议以赚取利息；
- 定期检查资产在 USDC 和 WETH 中的占比；
- 当比例偏离目标值 40%（USDC）/60%（WETH）超过 3% 缓冲区时，自动执行：
  - 从 Aave 提取多余资产；
  - 使用 Uniswap V3 进行代币兑换；
  - 重新将资产存入 Aave。

---

## 🧠 逻辑结构

### 1. 资产初始化与分配（`deposit.py`）

- 自动授权并调用 Aave Pool 的 `supply()` 方法将资产存入；
- 支持 USDC（6 decimals）和 WETH（18 decimals）；
- 调用 Aave 的 `getUserAccountData()` 获取用户当前的抵押数据。

### 2. 比例检查与再平衡（`rebalance.py`）

- 获取 USDC 和 WETH 的 aToken 余额；
- 使用链上预言机（Chainlink Price Feeds）获取当前美元价格；
- 判断当前资产占比是否超出设定阈值；
- 若偏离超过 `±3%`，自动执行再平衡操作：
  - 从 Aave 提取；
  - 使用 Uniswap V3 `exactInputSingle` 交换代币；
  - 使用 `quoteExactInputSingle` 获取报价，并设置滑点下限（70%）；
  - 再次调用 `deposit()` 重新投入。

### 3. 资产与合约设置（`setup_script.py`）

- 在本地/分叉网络中模拟初始环境，包括 mint USDC 和 deposit ETH 为 WETH；
- 查询并加载 Aave 协议中的 aToken 合约地址；
- 设置账户 ETH 余额、mint USDC 和 WETH。

---

## 🧪 本地运行说明

### 前置依赖

- Python 3.10+
- Boa 开发环境（建议使用 `virtualenv`）
- 已安装并配置好 `moccasin` 框架及合约

### 安装依赖

```bash
pip install boa moccasin
```

### 启动本地测试环境

确保你使用的是本地或 Fork 网络（如 Anvil 或 Hardhat）。

```bash
boa console
```

### 执行主脚本

```python
from script.rebalance import moccasin_main
moccasin_main()
```

---

## 📂 项目结构

```
├── script/
│   ├── deposit.py           # 初始资产投入 Aave
│   ├── rebalance.py         # 自动再平衡逻辑
│   ├── set_up_script.py     # 设置模拟网络中的资产
├── moccasin.config.py       # 加载当前网络配置
```

---

## ⚙️ 配置说明

确保 `manifest.json` 中配置了以下合约别名：

```json
{
  "usdc": "...",
  "weth": "...",
  "aave_PoolAddressesProvider": "...",
  "aave_Pool": "...",
  "aave_protocol_data_provider": "...",
  "uniswap_v3_router": "...",
  "uniswap_v3_quoter": "...",
  "usdc_price_feed": "...",
  "eth_price_feed": "..."
}
```

---

## ✅ TODOs

- [ ] 添加定时运行支持（如通过 Chainlink Automation）
- [ ] 添加策略参数配置（自定义比例/滑点）
- [ ] 接入 UI 前端控制台
- [ ] 增加跨资产支持，如 DAI/USDT 等

---

## 📜 License

MIT License © 2025 AutoTrand Contributors
