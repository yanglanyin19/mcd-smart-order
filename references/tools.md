# 麦当劳中国 MCP 连接器 · 工具参考

本技能通过「已连接的麦当劳 MCP 连接器」调用官方工具。以下为流程相关的工具说明，
完整工具清单以官方开放平台 `https://open.mcd.cn/mcp` 公布为准（当前约 30 个工具）。

## 连接配置（用户自行配置，技能不存储 Token）

协议：Streamable HTTP
地址：`https://mcp.mcd.cn`
请求头：`Authorization: Bearer YOUR_MCP_TOKEN`

> `YOUR_MCP_TOKEN` 由用户在开放平台「控制台」激活后复制，**请勿写入任何技能文件**。

客户端配置 JSON 示例：

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

连接后在 agent 中，这些工具以「已连接连接器」暴露，规范名为下表 `工具名`；
调用时按客户端约定加连接器前缀（如 `mcp__<连接器名>__<工具名>`）。本技能只引用规范名。

## 流程相关工具

| 工具名 | 输入要点 | 输出 / 用途 |
|--------|----------|-------------|
| `now-time-info` | 无 | 当前日期时间，用于判定上午/中午/下午 |
| `delivery-query-addresses` | 无 | 用户已存配送地址列表（用于默认定位） |
| `query-nearby-stores` | 地址文本 | 附近可用门店（含距离/门店编码） |
| `query-meals` | 门店编码 | 菜单：分类、餐品编码、标签（用于口味匹配） |
| `query-meal-detail` | 餐品编码 | 套餐组成、可替换项 |
| `query-store-coupons` | 门店编码 | 当前门店可用优惠券 |
| `available-coupons` | 无 | 麦麦省可领券列表 |
| `query-my-coupons` | 无 | 账户下已有券 |
| `calculate-price` | 商品列表(+券+就餐方式) | 商品金额、优惠、配送费、应付总价 |
| `create-order` | 门店/就餐方式/商品列表 | 订单详情 + 支付链接 |
| `query-my-account` | 无 | 积分账户（可作连接自检） |

## 错误码

| code | 含义 | 处理 |
|------|------|------|
| 401 | Token 无效/过期/未提供 | 检查 Authorization 头与 Token |
| 429 | 触发限流（>600 次/分钟） | 降低频率，合理间隔重试 |

## 合规

- 适用中国大陆（不含港澳台）；须同意《使用条款》及《麦当劳 MCP 服务规则》。
- 仅限非商业用途接入与使用；不得用于商业售卖、引流变现或违法违规用途。
- 本参考按「现状」提供，不构成对麦当劳商标的授权。
