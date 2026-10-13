# mcd-smart-order

一个**通用 agent 技能**：连接麦当劳中国官方 MCP 服务，帮用户就近找店、按口味/预算/人数智能选套餐或单点、叠加优惠券、对比堂食与外卖金额，并在用户确认后下单；同时维护本地点餐记忆，可在用户未明确口味/预算/人数时基于历史做推荐。

> 本技能为「纯流程 + 工具调用」技能，**不绑定任何特定客户端**，可在任意支持 MCP 连接器的 agent 客户端中使用。技能内**不包含、不存储任何 MCP Token**。

## 功能

1. **首连引导**：首次使用时检测连接器/账号；未连接则给出申请 Token 与配置连接器的步骤（不代做登录）。
2. **就近找店**：用已存配送地址默认定位并向用户确认，再查最近门店。
3. **需求采集**：收集口味、预算、人数；三项齐全走精算，缺失则走历史推荐 + 单人套餐轮询。
4. **选品比价**：套餐优先、单点补位，叠加优惠券，给出**堂食/外卖**两种金额；约束为「抵扣后金额 ≤ 预算 + 10 元」。
5. **确认后下单**：仅当用户明确确认才调用下单工具。
6. **记忆推荐**：点餐记录写入 `memory/order-history.csv`，按上午/中午/下午时段沉淀，支撑历史推荐。

## 目标用户

**主要适用人群**

| 人群 | 典型痛点 | 本技能如何解决 |
|------|----------|----------------|
| 上班族 / 学生等日常快餐用户 | 午休时间短，翻菜单、算优惠耗时 | 一句话给出需求，直接产出可下单组合与实付金额 |
| 价格敏感型用户 | 看不出叠加优惠券后的真实价格，堂食与外卖差价不清 | 叠加三类券后分别报出堂食 / 外卖金额，供比价取舍 |
| 有固定偏好的人群 | 每次都要重复描述口味与份量 | 本地记忆按 上午 / 中午 / 下午 时段沉淀历史，需求不全时自动做个性化推荐 |
| 团队里「点单的人」 | 要多人口味 + 总预算同时满足 | 支持按人数与口味配额组合，硬约束「实付 ≤ 预算 + 10 元」 |
| MCP 技能开发者 / 参赛者 | 缺少可参考的完整 workflow 实现 | 提供七步可复用流程与零依赖记忆脚本，作为一个通用 MCP 技能参考实现 |

**不适用场景**

- 企业团餐批量结算、需要发票与对公付款的场景（本技能面向个人点餐链路）。
- 中国大陆以外地区（含港澳台）的下单需求。
- 需要营养/医疗级膳食诊断的场景——本技能输出仅作餐品选择参考。

## 目录结构

```
mcd-smart-order/
├── SKILL.md                  # 技能主文件（工作流与规则）
├── README.md                 # 本文件（项目介绍 / 安装方法 / 使用示例 / 目标用户）
├── CONTEST_DECLARATION.md    # 参赛声明（原创性 / 合规 / 敏感信息 / 数据与责任）
├── MCP_INTEGRATION.md        # MCP Server、Tool 清单、调用流程与业务价值
├── workbuddy.md              # WorkBuddy 开发对话记录（已脱敏）
├── LICENSE                   # MIT License
├── references/
│   └── tools.md              # 连接器配置与工具参考
├── scripts/
│   └── order_memory.py       # 点餐记忆读写（stdlib，JSON 输出）
└── memory/
    └── order-history.csv     # 点餐记忆（表头已建，记录运行时追加）
```

## 安装方法

本技能**零第三方依赖**（记忆脚本仅用 Python 标准库），安装 = 放置技能目录 + 配置 MCP 连接器两步。

### 第 1 步：放置技能目录

把整个 `mcd-smart-order/` 目录放入你的 MCP 客户端所扫描的技能目录：

| 范围 | 目录 |
|------|------|
| 当前项目 | `<项目根>/.workbuddy/skills/mcd-smart-order/` |
| 当前用户（跨项目） | `~/.workbuddy/skills/mcd-smart-order/` |

保持目录结构不变（`references/`、`scripts/`、`memory/` 与 `SKILL.md` 同一层级），技能才能正确解析相对路径。

### 第 2 步：配置麦当劳 MCP 连接器

按下方「[连接麦当劳 MCP](#连接麦当劳-mcp用户自行操作)」配置自定义连接器（Streamable HTTP，`https://mcp.mcd.cn`，Bearer 鉴权）。**这是本技能的前置条件**，未配置时技能只输出首连指引。

### 第 3 步：验证

在对话中提一句「帮我查一下附近的麦当劳门店」或「随便推荐个单人套餐」，被正确触发即安装成功。

### 第 4 步：初始化点餐记忆（可选）

首次使用前可手动建表（不执行也会在首次写入时自动创建）：

```bash
python scripts/order_memory.py init
```

环境要求：MCP 客户端 + Python 3（仅记忆脚本需要）。无其他构建、安装或编译步骤。

## 前置条件

- 一个支持 **Streamable HTTP** 协议的 MCP 客户端。
- 一个中国大陆手机号，用于在 `https://open.mcd.cn/mcp` 登录并申请 MCP Token。

## 连接麦当劳 MCP（用户自行操作）

1. 打开 <https://open.mcd.cn/mcp>，用手机号验证登录。
2. 进入「控制台」激活并复制你的 MCP Token。
3. 在客户端添加一个自定义 MCP 连接器：
   - 传输方式：Streamable HTTP
   - URL：`https://mcp.mcd.cn`
   - Headers：`Authorization: Bearer <你的 Token>`
4. 保存并启用，连接器工具即可被本技能调用。

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_TOKEN"
      }
    }
  }
}
```

> 把 `YOUR_MCP_TOKEN` 替换成你复制的真实 Token 即可。Token 仅存在于你的客户端配置中，本技能仓库不保存。

## 使用方式

在对话中提到麦当劳点餐相关需求即可触发，例如：

- 「帮我点麦当劳，两个人吃，想吃鸡肉堡和牛肉堡，预算 70 元」
- 「附近有麦当劳吗？随便推荐个单人套餐」
- 「查下我这个地址能送的门店，按预算 50 给我凑单」

## 记忆字段

`memory/order-history.csv` 列：`date, time_slot, store, people, flavor, budget, dishes, drinks, amount_dinein, amount_takeout`
其中 `time_slot` 取值为 `上午 / 中午 / 下午`。读写统一通过 `scripts/order_memory.py`：

```bash
python scripts/order_memory.py init                         # 初始化 CSV
python scripts/order_memory.py suggest --slot 中午           # 该时段推荐种子
python scripts/order_memory.py history --slot 下午 --limit 5 # 查历史
python scripts/order_memory.py add --slot 中午 --people 2 --flavor 鸡肉堡/牛肉堡 \
       --budget 70 --dishes "..." --drinks "..." --dinein 68 --takeout 78
```

## 合规与安全

- 适用中国大陆地区（不含港澳台）；须遵守麦当劳中国《使用条款》及《麦当劳 MCP 服务规则》。
- 仅限个人非商业用途接入与使用；未经书面授权不得用于商业售卖、付费分发、引流变现或违法违规用途。
- 本仓库内容按「现状」提供，不构成任何保证，亦不构成对麦当劳及其关联方商标的授权。
- **本仓库不含任何密钥**：MCP Token 由用户自行配置，技能文件内仅以 `YOUR_MCP_TOKEN` 占位。
