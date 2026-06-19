# check-llm-pricing

Claude Code skill — 国产大模型定价监控。

自动采集国产大模型厂商（DeepSeek、阿里通义、字节豆包、百度文心、腾讯混元、智谱 AI、讯飞星火、百川智能、MiniMax、Kimi、小米等）的 API 定价、套餐订阅价格、新模型发布信息，生成可视化对比报告并推送至微信。

## 安装

```bash
git clone https://github.com/DawnCloud1213/check-llm-pricing.git \
  ~/.claude/skills/check-llm-pricing
```

## 依赖

| 组件 | 用途 | 必需 |
|------|------|------|
| `@playwright/mcp` 插件 | 采集 llmabacus.com 定价数据 | 是 |
| `@unlinearity/cli-wechat-bridge` MCP | 微信推送图片 | 否（无则本地留存） |

## 配置微信推送（可选）

无微信 MCP 时，报告文件保留在本地，skill 会告知文件路径。如需推送，按以下步骤配置：

### 1. 安装 wechat-bridge

```bash
npm install -g @unlinearity/cli-wechat-bridge
```

### 2. 配置 MCP 服务

在 `.claude.json` 中添加：

```json
{
  "mcpServers": {
    "wechat": {
      "command": "cmd",
      "args": ["/c", "node", "%APPDATA%\\npm\\node_modules\\@unlinearity\\cli-wechat-bridge\\dist\\wechat\\wechat-channel.js"],
      "type": "stdio"
    }
  }
}
```

macOS / Linux 用户将 `command` 改为 `"node"`，`args` 中去掉 `"/c"`。

### 3. 认证

重启 Claude Code 后，在对话中执行 `wechat_get_status`。按提示完成扫码登录。成功后 `~/.claude/channels/wechat/` 下会生成 `account.json` 和 `context_tokens.json`。

### 4. 安装发送脚本

```bash
mkdir -p ~/.claude/scripts
curl -o ~/.claude/scripts/wechat_send.py \
  https://raw.githubusercontent.com/DawnCloud1213/check-llm-pricing/master/scripts/wechat_send.py
```

### 5. 测试

```
python ~/.claude/scripts/wechat_send.py text "测试消息"
```

收到消息即配置成功。

## 用法

在 Claude Code 中：
```
检查大模型定价
```

## 输出

- 单页 HTML 报告 + 截图 → `report_YYYY-MM-DD.html` / `report.png`
- 微信推送（文字直连 API + 图片 MCP）
- 结构化 JSON → `latest.json` + `history.jsonl`

## 安全审查

✅ 通过 — 无硬编码凭据、无 PII 泄露。路径使用 `~` 引用。
