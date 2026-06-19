# check-llm-pricing

Claude Code skill — 国产大模型定价监控。

自动采集国产大模型厂商（DeepSeek、阿里通义、字节豆包、百度文心、腾讯混元、智谱 AI、讯飞星火、百川智能、MiniMax、Kimi、小米等）的 API 定价、套餐订阅价格、新模型发布信息，生成可视化对比报告并推送至微信。

## 用法

在 Claude Code 中：
```
检查大模型定价
```

## 数据源

- **API 定价**：[llmabacus.com](https://www.llmabacus.com)（Playwright 提取）
- **新模型新闻**：WebSearch 多轮搜索
- **套餐订阅**：WebSearch

## 输出

- 单页 HTML 报告 + 截图
- 微信推送（文字直连 API + 图片 MCP）
- 结构化 JSON 数据存档

## 安装

```bash
# 克隆到 Claude Code skills 目录
git clone https://github.com/DawnCloud1213/check-llm-pricing.git \
  ~/.claude/skills/check-llm-pricing
```
