# Resume Analyzer AI

> 基于 Multi-Agent + RAG 的智能简历分析工具
>
> 上传 PDF 简历 + 粘贴 JD，AI 自动分析匹配度、找出技能缺口、给出针对性优化建议并重写简历关键段落。

---

## 产品背景

投了简历之后已读不回，不知道是岗位招满了还是简历不符合条件——这是求职过程中最普遍的痛点。

Resume Analyzer AI 在投简历之前帮你做一次「预审」：分析你的简历和目标 JD 的匹配程度，找出缺口，告诉你哪里要改、怎么改。

---

## 功能特性

- **PDF 简历解析**：上传 PDF，自动提取文本内容
- **JD 深度分析**：提取核心要求、必备技能、加分项
- **RAG 知识库**：向量检索 + Reranker 精排，检索相似岗位历史数据作参考
- **匹配度评分**：ReAct Agent 自主调用工具查市场数据，输出 0-100 匹配分 + 技能缺口
- **条件路由**：高匹配（≥75）直接重写简历；低匹配走完整建议流程
- **Multi-Agent 并行建议**：Supervisor 决策分发，技能缺口 / 表达优化 / 投递策略三个子 Agent 并行执行
- **简历重写**：针对目标 JD，重写简历关键段落
- **流式输出**：SSE 实时展示分析过程
- **可观测性**：Langfuse 追踪完整调用链路
- **评测框架**：LLM-as-Judge 自动化评估建议质量

---

## 技术栈

### 前端

| 模块     | 技术                         |
| -------- | ---------------------------- |
| 框架     | React 18 + Vite + TypeScript |
| 样式     | Tailwind CSS                 |
| 状态管理 | Zustand                      |
| HTTP     | Axios                        |

### 后端

| 模块     | 技术                              |
| -------- | --------------------------------- |
| Web 框架 | FastAPI + Uvicorn                 |
| AI 框架  | LangChain + LangGraph             |
| AI 模型  | Anthropic Claude（via DashScope） |
| RAG      | pgvector + PostgreSQL             |
| PDF 解析 | PyMuPDF                           |
| 运行时   | Python 3.11+                      |

### 部署

| 模块     | 技术                    |
| -------- | ----------------------- |
| 容器化   | Docker + docker-compose |
| 服务器   | AWS EC2                 |
| 反向代理 | Nginx                   |

---

## 系统流程

```
用户上传 PDF + 粘贴 JD
        │
        ▼
   jd_analysis          提取 JD 核心要求、必备技能、加分项
        │
        ▼
   rag_retrieval         向量检索 + Reranker 精排，找相似岗位作参考
        │
        ▼
   match_analysis        ReAct Agent：自主调用工具查市场数据
   （Tool Use）          输出匹配分 + 已匹配技能 + 缺失技能
        │
   [条件路由]
        ├─ 分数 ≥75 ──────────────────────────────────────┐
        │                                                  │
        └─ 分数 <75                                        │
              │                                            │
              ▼                                            │
          supervisor    LLM 决策：启动哪几个子 Agent        │
              │                                            │
         [并行 fan-out]                                    │
        ┌────┼────┐                                        │
        ▼    ▼    ▼                                        │
   skill_ expr_ strat_  三个子 Agent 并行执行              │
   _gap   ess   egy     技能缺口 / 表达优化 / 投递策略      │
        └────┼────┘                                        │
             ▼                                             │
   aggregate_suggestions 汇总三路结果                      │
             │                                             │
             └──────────────────────┬────────────────────┘
                                    │
                                    ▼
                                 rewrite    针对 JD 重写简历关键段落
                                    │
                                   END
```

---

## 项目结构

```
resume-analyzer/
  frontend/                  React + Vite 前端
    src/
      api/
        analyze.ts           API 调用封装
      components/
        UploadForm.tsx        简历上传 + JD 输入表单
        AnalysisResult.tsx   分析结果展示
        MatchScore.tsx       匹配度评分组件
        SkillTags.tsx        技能标签组件
      types/
        index.ts             TypeScript 类型定义
      App.tsx
      main.tsx
    package.json
    vite.config.ts

  backend/                   Python + FastAPI 后端
    main.py                  FastAPI 入口 + SSE 流式响应
    graph.py                 LangGraph 图定义（节点 + 路由 + 编译）
    state.py                 ResumeAnalysisState 类型定义
    tools.py                 LangChain 工具（PDF 解析 / 市场搜索）
    rag.py                   RAG 知识库（Embedding + 向量检索 + Reranker）
    db.py                    数据库连接管理
    init_db.py               数据库初始化脚本
    eval/
      run_eval.py            LLM-as-Judge 评测脚本
      fixtures.py            评测测试用例
    pyproject.toml
    .env.example

  docker-compose.yml         统一编排前后端
  README.md
```

---

## 快速开始

### 环境要求

- Node.js >= 18
- Python >= 3.11
- PostgreSQL >= 14（需要 pgvector 插件）

### 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Key


# 1. 第一次部署时初始化数据库（只需要跑一次）

python init_db.py

# 启动服务
uvicorn main:server --reload --port 8000

```

### 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动
npm run dev
# 访问 http://localhost:5173
```

### Docker 一键启动

```bash
# 根目录下
docker-compose up -d --build
```

---

## API 文档

### POST /api/analyze

上传简历并分析匹配度。

**请求（multipart/form-data）：**

```
resume: File（PDF 格式）
jd: string（JD 文本）
```

**响应（SSE 流式）：**

```
data: {"type": "step", "step": "jd_analysis", "content": "..."}
data: {"type": "step", "step": "match_score", "content": "..."}
data: {"type": "step", "step": "suggestions", "content": "..."}
data: {"type": "step", "step": "rewrite", "content": "..."}
data: {"type": "done", "content": "..."}
```

### POST /api/knowledge

向 RAG 知识库添加 JD 数据。

```json
{
  "title": "岗位名称",
  "content": "JD 全文"
}
```

### GET /health

服务健康检查。

---

## License

MIT
