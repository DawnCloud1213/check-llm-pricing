# check-llm-pricing

Claude Code skill — 国产大模型定价监控。

自动采集国产大模型厂商（DeepSeek、阿里通义、字节豆包、百度文心、腾讯混元、智谱 AI、讯飞星火、百川智能、MiniMax、Kimi、小米等）的 API 定价、套餐订阅价格、新模型发布信息，生成对比报告并**自动选择可用推送通道**送达。

## 推送通道

| 通道 | 文本 | 图片 | 文件 | 方式 |
|------|:----:|:----:|:----:|------|
| Telegram | ✅ | ✅ | ✅ | 直连脚本（内置代理） |
| 微信 (iLink Bot) | ✅ | ✅ | ✅ | MCP + 直连 API 预热 |
| 飞书 | ✅ | ❌ | ❌ | Webhook 直连 |
| 本地文件（降级） | — | — | — | 报告留存本地 |

**自动选择**：按用户记忆偏好 → Telegram → 微信 → 飞书 → 本地降级。通道失败自动容错到下一通道。

## 安装

```bash
git clone https://github.com/DawnCloud1213/check-llm-pricing.git \
  ~/.claude/skills/check-llm-pricing
```

## 依赖

| 组件 | 用途 | 必需 |
|------|------|------|
| `@playwright/mcp` 插件 | 采集 llmabacus.com 定价数据 | 是 |
| 推送通道相关脚本/MCP | 发送报告（见上方表格） | 否（无则本地留存） |

## 配置推送通道

### Telegram（推荐）

```bash
# 确保 ~/.claude/channels/telegram/.env 存在
echo "TELEGRAM_BOT_TOKEN=your_token" > ~/.claude/channels/telegram/.env
```

### 微信

参考 `@unlinearity/cli-wechat-bridge` 文档配置 MCP，扫码登录后自动生成凭证。

### 飞书

将群机器人 Webhook URL 写入 `~/.claude/channels/feishu/config.json`。

## 用法

在 Claude Code 中：
```
检查大模型定价
```

## 输出

- 单页 HTML 报告 + 截图 → `report_YYYY-MM-DD.html` / `report.png`
- 自动推送至可用通道（文字摘要 + 图片）
- 结构化 JSON → `latest.json` + `history.jsonl`

## 记忆偏好

用户可保存推送偏好，下次自动优先：

```
remember name="push-preference" body="首选推送通道为 Telegram"
```
