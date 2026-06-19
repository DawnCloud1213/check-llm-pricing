---
name: check-llm-pricing
description: 抓取国产大模型厂商的新模型信息、API 按量付费价格、套餐订阅价格，生成对比报告并以图片形式推送至微信。
triggers:
  - 检查大模型定价
  - 大模型价格对比
  - 国产模型定价
  - 模型比价
  - check LLM pricing
  - 大模型调价
  - AI模型价格
---

# 国产大模型定价监控

自动化采集国产大模型厂商的 API 定价、套餐订阅价格、新模型发布信息，生成可视化对比报告。

## 核心规则

### 模型强制

**全流程所有阶段均使用 haiku 模型**，不得使用 sonnet/opus。本任务数据量大但逻辑简单，haiku 完全胜任，成本可降低 20x+。

### Playwright 强制

**必须使用官方 Playwright**（`mcp__plugin_playwright_playwright__*`，即 `@playwright/mcp` 插件）。**禁止使用 ECC Playwright**（`mcp__plugin_everything-claude-code_playwright__*`）。

> **环境要求**：内置 Playwright MCP 需配置 `--user-data-dir` 指向持久化目录，否则 Chrome 每次弹窗询问自动化权限。详见 Playwright MCP 官方文档 Browser Configuration 章节。

### 子代理架构

**所有数据采集和 Playwright 操作均通过子代理（Agent 工具）执行**，主代理仅负责编排调度、数据整合和最终推送。每个子代理必须指定 `model: "haiku"`。

| 阶段 | 执行方 | 原因 |
|------|--------|------|
| Phase 1 (Playwright 采集) | haiku 子代理 | 独立的浏览器自动化任务，隔离 Playwright 状态 |
| Phase 2 (Web 搜索) | haiku 子代理 (并行) | 独立搜索任务，无共享状态，天然可并行 |
| Phase 3 (整合对比) | 主代理 | 轻量 JSON 比对，无需子代理 |
| Phase 4 (HTML 生成) | `frontend-design` 技能 | 专业前端设计能力，产出精美报告 |
| Phase 5 (保存推送) | 主代理 | 纯工具调用，无需 LLM |

> **原则**：凡涉及外部 I/O（浏览器、网络搜索）的操作均委派给 haiku 子代理，主代理只做纯数据编排。

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
使用 Playwright 完成以下任务（所有操作使用 mcp__plugin_playwright_playwright__* 工具）：

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

### Phase 4: 生成报告 HTML（frontend-design 技能）

**调用 `frontend-design` 技能**生成单个完整报告 HTML 文件 `report_YYYY-MM-DD.html`，保存至 `A:\JUST_DO_IT\llm-pricing-monitor\`。以下为设计模板规范：

**全局：**
- 背景纯白 `#fff`，字体 `Noto Sans SC`
- `.container`：`max-width: 1280px; margin: 0 auto`（居中容器，白底无可见留白）
- `body`：`font-size: 17px; padding: 16px 20px`

**标题区：**
1. 4px 蓝色渐变条 `linear-gradient(90deg, #1a56db, #3b82f6, #60a5fa, #93c5fd)`
2. h1：`font-size: 30px; font-weight: 800; color: #0f2b4c`
3. 副标题：`font-size: 15px; color: #64748b`

**摘要区：**
- 四宫格 `grid-template-columns: repeat(4, 1fr); gap: 10px`
- 卡片：`padding: 16px 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,.04); border: 1px solid #e8ecf1`
- 数值：`font-size: 42px; font-weight: 800; color: #0f2b4c`
- 标签：`font-size: 14px; color: #94a3b8`

**表格：**
- `font-size: 15px`，表头 `font-size: 14px; font-weight: 700; background: #f0f4ff`
- 斑马纹：`tr:nth-child(even) td { background: #fafbfd }` + `tr:hover td { background: #f0f7ff }`
- 单元格：`padding: 10px 14px; border-bottom: 1px solid #f1f5f9`
- 标签：`font-size: 12px; font-weight: 600; padding: 3px 8px; border-radius: 4px`

**卡片（套餐/趋势）：**
- 阴影 `box-shadow: 0 2px 8px rgba(0,0,0,.04); border-radius: 10px; border: 1px solid #e8ecf1`
- 趋势卡片左侧 4px 蓝色边框 `border-left: 4px solid #3b82f6`

**时序：**
- 左侧 2px 蓝色竖线 + 圆点标记
- 条目间距 `margin-bottom: 12px`

**板块结构：**
1. 标题栏 + 标题 + 副标题
2. 四宫格摘要卡（厂商数/模型数/价格变动/新模型数）
3. API 定价表（厂商/模型/输入价/输出价/缓存价/上下文/标签，带价格变动标记）
4. 套餐订阅卡片 grid
5. 新模型发布时间线
6. 行业趋势卡片 grid

### Phase 5: 截图与推送（主代理 + haiku 子代理）

**截图**（haiku 子代理）：
```
启动 python -m http.server 8899 --directory "A:\JUST_DO_IT\llm-pricing-monitor"

1. browser_navigate → http://localhost:8899/report_YYYY-MM-DD.html
2. 等待 2 秒渲染 (browser_wait_for time=2)
3. browser_evaluate 测量页面：() => ({ w: Math.ceil(document.body.scrollWidth), h: Math.ceil(document.body.scrollHeight) })
4. browser_resize 到测量值（width=w+10, height=h+20，避免滚动条）
5. browser_take_screenshot fullPage=true → report.png（保存至桌面，再 cp 到报告目录）
```

> **视口策略**：由于模板使用 `max-width: 1280px` 居中，将视口缩至内容宽度（约 1315px）可消除截图两侧白边，同时使文字占画面比例最大化。
>
> **文件路径**：Playwright MCP 仅允许写入桌面和 `.playwright-mcp` 目录，截图后需 `cp` 到目标目录。
>
> **2x 分辨率**：`@playwright/mcp` 截图硬编码 `scale: 'css'`（1x）。如需 retina 截图，需修改 MCP 源码或等待官方支持 `scale: 'device'`。

截完 `taskkill` 服务器。

**推送**（主代理）：
1. 保存 `latest.json` + 追加 `history.jsonl`
2. **文字摘要**（直连 API，无 token 风险）：
   `python C:\Users\DawnCloud\.claude\scripts\wechat_send.py text "claude code：\n摘要…"`
3. **截图**（MCP）：
   `wechat_send_image report.png`

> **推送策略**：文本走直连 API（`wechat_send.py text`），此调用的副作用是唤醒服务端 session，后续 MCP 发图无需额外预热。

## 模型使用规则

| 阶段 | 执行方 | 模型 | 原因 |
|------|--------|------|------|
| Phase 1 (API定价采集) | haiku 子代理 | haiku | Playwright 提取 + 数据格式化 |
| Phase 2 (新闻/套餐搜索) | haiku 子代理 ×2 | haiku | WebSearch + 文本提取，并行 |
| Phase 3 (整合对比) | 主代理 | haiku | JSON 比对，纯数据处理 |
| Phase 4 (HTML 生成) | `frontend-design` 技能 | 技能默认 | 专业前端设计 |
| Phase 5 (截图) | haiku 子代理 | haiku | Playwright 单张全页面截图 |
| Phase 5 (推送) | 主代理 | 无需 LLM | MCP 推送 |

> 全流程 haiku，零例外。

## 子代理调度速查

```
Phase 1: Agent(general-purpose, haiku, "采集 llmabacus API 定价", prompt="...")

Phase 2: 同一条消息并行发送：
  Agent(general-purpose, haiku, "搜索新模型新闻", prompt="...")
  Agent(general-purpose, haiku, "搜索套餐定价", prompt="...")

Phase 5 截图: Agent(general-purpose, haiku, "截图报告", prompt="测量尺寸并 fullPage 截图...")
```

## 推送速查

```
# 文字 — 直连 API（同时唤醒 session，后续 MCP 无需预热）
python wechat_send.py text "claude code：
📊 摘要…"

# 图片 — MCP（文本已唤醒 session，直接发）
wechat_send_image report.png
```

## 报告存档

```
A:\JUST_DO_IT\llm-pricing-monitor\
  ├── latest.json              ← 最新结构化数据
  ├── history.jsonl             ← 追加式历史
  ├── report_YYYY-MM-DD.html   ← 单页完整报告
  └── report.png               ← 报告截图
```

## 注意事项

1. **llmabacus.com 是 Next.js SPA**，必须用 Playwright 渲染后提取，不能用 WebFetch
2. 价格单位为"元/百万 tokens"，核价日期从页面提取
3. 首次运行无历史数据时跳过 Phase 3 对比步骤
4. **Playwright**：始终用 `mcp__plugin_playwright_playwright__*`，禁用 ECC 版本
5. **模型**：全流程 haiku，禁止使用 sonnet/opus
6. **子代理隔离**：Phase 1-2 和 Phase 5 截图必须通过子代理
7. **并行优先**：Phase 2 两个搜索子代理同一消息发出
8. **HTML 模板**：白底 + `max-width: 1280px` 居中 + 视口缩至内容宽度（~1315px）截图，消除白边
9. **推送**：文字 `wechat_send.py text`（直连 API，同时唤醒 session），图片 `wechat_send_image`（MCP，利用文本调用已唤醒的 session）
