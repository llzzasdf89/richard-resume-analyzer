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
- **匹配度评分**：0-100 分，直观展示简历和 JD 的契合程度
- **技能缺口分析**：明确列出匹配点和缺失点
- **RAG 知识库**：检索相似岗位历史数据，提供更精准的参考
- **优化建议**：结合匹配分析和知识库，生成针对性改进建议
- **简历重写**：针对目标 JD，重写简历关键段落
- **流式输出**：SSE 实时展示分析过程

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

## Multi-Agent 架构

```
用户上传 PDF + 粘贴 JD
  ↓
[PDF 解析节点]      提取简历文本，存入 State
  ↓
[JD 分析 Agent]    提取核心要求、必备技能、加分项
  ↓
[RAG 检索节点]     检索相似岗位历史数据作为参考
  ↓
[匹配分析 Agent]   匹配度评分 + 匹配点 + 技能缺口
  ↓
[优化建议 Agent]   结合匹配分析 + RAG，生成针对性建议
  ↓
[简历重写 Agent]   针对 JD 重写简历关键段落
  ↓
流式输出结果
```

---

## 项目结构

```
resume-analyzer/
  frontend/                  React + Vite 前端
    src/
      components/            UI 组件
      pages/                 页面
      types/                 TypeScript 类型
      api/                   API 调用封装
    package.json
    vite.config.ts

  backend/                   Python + FastAPI 后端
    main.py                  FastAPI 入口
    graph.py                 LangGraph 核心逻辑
    state.py                 自定义 State
    tools.py                 工具函数
    rag.py                   RAG 知识库
    requirements.txt
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

## 相关项目

- [Code Reviewer AI（Next.js 版）](https://github.com/llzzasdf89/richard-code-reviewer) — 线上：[richard-code-reviewer.xyz](https://richard-code-reviewer.xyz)
- [Code Reviewer AI（Python 版）](https://github.com/llzzasdf89/richard-code-reviewer-python)

---

## License

MIT
