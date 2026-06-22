---
name: check-llm-pricing
description: 抓取国产大模型厂商的新模型信息、API 按量付费价格、套餐订阅价格，生成对比报告并多通道推送。
triggers:
  - 检查大模型定价
  - 大模型价格对比
  - 国产模型定价
  - 模型比价
  - check LLM pricing
  - 大模型调价
  - AI模型价格
  - 查询大模型价格
---

# 国产大模型定价监控

自动化采集国产大模型厂商的 API 定价、套餐订阅价格、新模型发布信息，生成可视化对比报告。

## 前置条件

- **Playwright**：`@playwright/mcp` 插件（`mcp__playwright__*`），用于采集 llmabacus.com 定价数据。
- **推送通道**（均为可选）：模块自动检测以下通道并选择可用者推送，无需手动指定。

## 核心规则

### 模型强制

**全流程所有阶段均使用 haiku 模型**，不得使用 sonnet/opus。本任务数据量大但逻辑简单，haiku 完全胜任，成本可降低 20x+。

### Playwright 强制

**必须使用官方 Playwright**（`mcp__playwright__*` 工具集）。**禁止使用 ECC Playwright**（`mcp__plugin_everything-claude-code_playwright__*`）。

> **环境要求**：内置 Playwright MCP 需配置 `--user-data-dir` 指向持久化目录，否则 Chrome 每次弹窗询问自动化权限。详见 Playwright MCP 官方文档 Browser Configuration 章节。

### 子代理架构

**所有数据采集和 Playwright 操作均通过子代理（Agent 工具）执行**，主代理仅负责编排调度、数据整合和最终推送。每个子代理必须指定 `model: "haiku"`。

| 阶段 | 执行方 | 原因 |
|------|--------|------|
| Phase 1 (Playwright 采集) | haiku 子代理 | 独立的浏览器自动化任务，隔离 Playwright 状态 |
| Phase 2 (Web 搜索) | haiku 子代理 (并行) | 独立搜索任务，无共享状态，天然可并行 |
| Phase 3 (整合对比) | 主代理 | 轻量 JSON 比对，无需子代理 |
| Phase 4 (HTML 生成 / 摘要) | 主代理（或 `frontend-design` 技能） | 两种输出模式（见下文） |
| Phase 5 (保存推送) | 主代理 | 纯工具/脚本调用，无需 LLM |

> **原则**：凡涉及外部 I/O（浏览器、网络搜索）的操作均委派给 haiku 子代理，主代理只做纯数据编排。

### 推送通道检测与优先级

本 Skill **自动检测所有可用推送通道**，按以下优先级选择：

```
优先级 1: 用户记忆偏好（通过 memory 工具查询 "push-preference"）
优先级 2: 具备 MCP 工具的通道（WeChat MCP / Telegram MCP）
优先级 3: 具备直连脚本的通道（Telegram / Feishu / WeChat 直连 API）
优先级 4: 降级为本地文件 + 告知用户路径
```

**检测方式**（Phase 5 开始时执行）：

1. **读取记忆**：调用 `memory search --query "push preference"` 和 `memory search --query "推送"`，查找用户之前保存的推送偏好。
2. **检测 MCP 工具**：在当前工具列表中搜索包含键名的工具（如 `wechat_notify`、`wechat_send_image`、`telegram__send_message`）。
3. **检测通道凭证文件**：检查 `~/.claude/channels/` 下各子目录的存在性（`wechat/`、`telegram/`、`feishu/`）并验证凭证完整性。
4. **检测推送脚本**：检查 `~/.claude/scripts/` 下是否存在 `wechat_send.py`、`telegram_send.py`、`feishu_send.py`。
5. **生成通道可用性清单**：综合上述检查，记录每个通道的支持能力（文本/图片/文件）。

**推送执行规则**：

- 按优先级尝试：先试最高优先级通道
- 每个通道发送**文字摘要**，若通道支持图片则追加发送**报告截图**
- 当前通道失败（异常/超时/返回错误）则**自动降级到下一通道**
- 全部通道均不可用时，告知用户文件路径
- **不重复发送**：一条通道成功发送后，不尝试其余通道（除非 `force_multi_push` 标记）

---

## 推送通道速查

### 1. 微信 WeChat（iLink Bot）

| 能力 | 方式 | 命令 |
|------|------|------|
| 文本 | 直连 API 脚本 | `python ~/.claude/scripts/wechat_send.py text "内容"` |
| 图片 | MCP 工具 | `mcp__wechat__wechat_send_image {path}` |
| 文件 | MCP 工具 | `mcp__wechat__wechat_send_file {path}` |

**注意事项**：
- `context_token` 闲置约 1-2 天后失效，发送前需预热
- 预热脚本：`python ~/.claude/scripts/wechat_warmup.py`
- 预热成功后再调用 MCP 发送工具
- 若预热失败，token 已过期，需用户重新扫码

### 2. Telegram Bot

| 能力 | 方式 | 命令 |
|------|------|------|
| 文本 | 直连脚本（走代理） | `python telegram_send.py text "内容"` |
| 图片 | 直连脚本（走代理） | `python telegram_send.py photo <path> [标题]` |
| 文件 | 直连脚本（走代理） | `python telegram_send.py file <path> [标题]` |

**注意事项**：
- MCP 的 Telegram 工具因 GFW 直连不可用，必须用直连脚本（内置代理）
- Token 永不过期，零维护
- 预设：Bot @Hbc_graduation_project_bot → 用户 @DawnCloud1213 (chat_id=8018758219)
- 代理：`http://127.0.0.1:7897`
- 脚本路径：`~/.claude/scripts/telegram_send.py`

### 3. 飞书 Feishu

| 能力 | 方式 | 命令 |
|------|------|------|
| 文本 | Webhook 直连 | `python feishu_send.py text "内容"` |
| 富文本 | Webhook 直连 | `python feishu_send.py post "标题" "[[段落]]"` |

**注意事项**：
- 群自定义机器人 Webhook，不支持图片/文件
- 永不过期，国内可直连
- 脚本路径：`~/.claude/scripts/feishu_send.py`

### 4. 降级：本地文件

当所有推送通道不可用时：
- 告知用户文件路径：`report_YYYY-MM-DD.html`、`report.png`、`latest.json`
- 路径：`A:\JUST_DO_IT\llm-pricing-monitor\`

---

## 数据源策略

### 主数据源：llmabacus.com

`https://www.llmabacus.com` 已覆盖全部国产厂商的 API 定价（每日自动核价），包含：DeepSeek、阿里通义、字节豆包、百度文心、腾讯混元、智谱 AI、讯飞星火、百川智能、MiniMax、Moonshot/Kimi、小米。

### 辅数据源

**新模型发布新闻**：WebSearch 搜索 `"国产大模型 新模型 发布 2026年X月"`（使用当前月份）

**套餐/订阅定价**：WebSearch 搜索 `"豆包 智谱 Kimi 文心 小米 订阅套餐 价格 2026"`

## 执行流程

### Phase 1: 采集 API 定价（haiku 子代理）

**派发一个 haiku 子代理**完成 Playwright 数据采集。子代理 prompt：

```
使用 Playwright 完成以下任务（所有操作使用 mcp__playwright__* 工具）：

1. browser_navigate → https://www.llmabacus.com
2. 等待 3 秒让 SPA 渲染完成 (browser_wait_for time=3)
3. browser_evaluate 执行 JS 提取全部 table 数据：
   () => {
     const table = document.querySelector('table');
     if (!table) return null;
     const rows = table.querySelectorAll('tr');
     return Array.from(rows).map(row => {
       const cells = row.querySelectorAll('td, th');
       return Array.from(cells).map(c => c.innerText.trim());
     });
   }
4. 解析返回值，过滤出国产厂商（排除 OpenAI/Anthropic/Google/xAI）
5. 以 JSON 格式返回结构化数据，格式如下：
[
  {
    "厂商": "DeepSeek",
    "模型": "V4 Pro",
    "输入价格": "¥3.00",
    "输出价格": "¥6.00",
    "缓存价格": "¥0.03",
    "上下文": "1.0M",
    "最大输出": "384K",
    "标签": "旗舰/推理/长上下文"
  },
  ...
]
```

调用方式：`Agent` 工具，`subagent_type: "general-purpose"`, `model: "haiku"`，`description: "采集 llmabacus API 定价"`

子代理返回后，主代理解析 JSON 结果。

### Phase 2: 搜索新闻与套餐（haiku 子代理，并行两个）

**同时派发两个 haiku 子代理**，互不依赖，并行执行。

**子代理 A — 新模型新闻（两轮搜索，防遗漏）**：
```
使用 WebSearch 分两轮搜索，提取国产大模型新模型发布信息。

第一轮 — 泛搜索：
搜索词："国产大模型 新模型 发布 2026年<当前月份>月"

第二轮 — 逐厂商补搜（必须逐条搜索以下 7 组，每条一个 WebSearch 调用）：
搜索词1："智谱 GLM 新模型 发布 2026年6月"
搜索词2："DeepSeek 新模型 发布 2026年6月"
搜索词3："阿里 通义千问 Qwen 新模型 发布 2026年6月"
搜索词4："MiniMax 新模型 发布 2026年6月"
搜索词5："讯飞 星火 Spark 新模型 发布 2026年6月"
搜索词6："字节 豆包 百川 Kimi 腾讯 混元 新模型 发布 2026年6月"
搜索词7："小米 MiLM 大模型 发布 2026年6月"

从两轮搜索结果中合并去重，提取结构化信息，返回 JSON：
{
  "新模型": [
    {"厂商": "", "模型": "", "发布日期": "", "关键特性": ""}
  ]
}

要求：
- 覆盖全部 11 家国产厂商：DeepSeek、阿里通义、字节豆包、百度文心、腾讯混元、智谱 AI、讯飞星火、百川智能、MiniMax、Kimi、小米
- 同时关注新入局者：华为、云知声、昆仑万维等
- 两轮搜索结果合并后去重（同一模型只保留一条）
- 仅提取当前月及上月下旬的发布
- 按发布日期降序排列
- 如厂商无新发布，不强行编造
```

**子代理 B — 套餐/订阅定价**：
```
使用 WebSearch 搜索以下内容，提取国产大模型 C 端订阅套餐和 API 套餐定价：

搜索词："豆包 智谱 Kimi 文心 订阅套餐 价格 2026"

从搜索结果中提取结构化信息，返回 JSON：
{
  "套餐": [
    {"厂商": "", "套餐名": "", "月费": "", "年费": "", "Token额度": "", "特点": ""}
  ]
}

要求：
- 覆盖字节豆包、智谱 AI、Kimi、百度文心、MiniMax、小米等
- 区分 C 端订阅套餐和 API 资源包
- 标注价格时效性（如"6月下旬上线"）
- 按厂商分组，月费升序
```

调用方式：两个 `Agent` 调用放在同一消息中，`subagent_type: "general-purpose"`, `model: "haiku"`，系统自动并行执行。

### Phase 3: 数据整合与历史对比（主代理）

1. 加载上次报告：读取 `A:\JUST_DO_IT\llm-pricing-monitor\latest.json`
2. 整合 Phase 1 和 Phase 2 的子代理返回结果
3. 逐模型对比历史数据：
   - 🆕 新增模型（上次报告中不存在）
   - 🔴 涨价（输出价格上升）
   - 🟢 降价（输出价格下降）
   - ⚪ 不变
4. 统计变更摘要：降价项数、涨价项数、新增模型数

### Phase 4: 生成输出（两种模式）

**模式 A — 完整 HTML 报告**（当 Playwright 可用且需要截图时）：
- 调用 `frontend-design` 技能生成 `report_YYYY-MM-DD.html`
- 通过 Playwright 截图 → `report_YYYY-MM-DD.png`
- 设计模板同原规范（白底、max-width:1280px、蓝色渐变色、四宫格摘要等）

**模式 B — 纯文本摘要**（当仅需推送文字时，性能更优）：
- 主代理直接编译文本摘要，无需子代理
- 包含：涨价/降价/新增模型统计、最便宜TOP3、旗舰对比、新模型清单、套餐推荐

### Phase 5: 保存与多通道推送（主代理）

**第一步：检测可用推送通道**

按以下顺序检测，生成通道可用性清单：

```python
channels = {}

# 1. 检测记忆偏好
pref = memory_search("push preference")  # 若有，作为第一优先级

# 2. 检测微信 WeChat
if os.path.exists("~/.claude/channels/wechat/account.json"):
    channels["wechat"] = {"text": True, "image": True, "file": True}

# 3. 检测 Telegram
if os.path.exists("~/.claude/channels/telegram/.env"):
    channels["telegram"] = {"text": True, "image": True, "file": True}

# 4. 检测飞书 Feishu
if os.path.exists("~/.claude/channels/feishu/config.json"):
    channels["feishu"] = {"text": True, "image": False, "file": False}
```

**第二步：按优先级发送**

```
优先级排序（根据记忆偏好 + 可用性 + 能力）：
1. 用户记忆偏好的通道（如有）
2. Telegram（Token 永不过期，支持图片/文件）
3. WeChat MCP（需预热，支持图片/文件）
4. 飞书（仅文字）
5. 本地文件（最终降级）
```

**微信发送流程**（示例）：
```python
# 预热
run("python ~/.claude/scripts/wechat_warmup.py")

# 发送文字
result = mcp__wechat__wechat_notify(message="claude code：\n📊 摘要...")

# 若通道支持图片且有 report.png，追加发送
mcp__wechat__wechat_send_image(path="report.png")
```

**Telegram 发送流程**（示例）：
```python
# 发送文字
run("python ~/.claude/scripts/telegram_send.py text \"消息内容\"")

# 发送图片（如有）
run("python ~/.claude/scripts/telegram_send.py photo report.png \"报告标题\"")
```

**飞书发送流程**（示例）：
```python
# 仅文字（不支持图片）
run("python ~/.claude/scripts/feishu_send.py text \"消息内容\"")
```

**第三步：保存数据**
- 保存 `latest.json` 覆盖
- 追加 `history.jsonl`
- 若生成了 HTML，保存 `report_YYYY-MM-DD.html`

## 输出存档

```
A:\JUST_DO_IT\llm-pricing-monitor\
  ├── latest.json              ← 最新结构化数据
  ├── history.jsonl             ← 追加式历史
  ├── report_YYYY-MM-DD.html   ← 单页完整报告（模式 A）
  └── report_YYYY-MM-DD.png    ← 报告截图（模式 A）
```

## 注意事项

1. **llmabacus.com 是 Next.js SPA**，必须用 Playwright 渲染后提取，不能用 WebFetch
2. 价格单位为"元/百万 tokens"，核价日期从页面提取
3. 首次运行无历史数据时跳过 Phase 3 对比步骤
4. **Playwright**：始终用 `mcp__playwright__*` 工具集
5. **模型**：全流程 haiku，禁止使用 sonnet/opus
6. **子代理隔离**：Phase 1-2 必须通过子代理
7. **并行优先**：Phase 2 两个搜索子代理同一消息发出
8. **推送容错**：当前通道失败自动降级下一通道，不重复发送
9. **记忆偏好**：用户可通过 `remember` 工具保存推送偏好（如 `remember name="push-preference" body="首选推送通道为 Telegram"`），下次运行时自动优先
