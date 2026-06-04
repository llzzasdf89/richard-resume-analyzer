TEST_CASES = [
    {
        "name": "高匹配：React前端 vs 前端岗位",
        "expected_score_range": (70, 95),
        "expected_matched": ["React", "TypeScript"],
        "expected_missing_not_contains": ["React"],  # 高匹配不该缺React
        "resume_text": """
姓名：张三
技能：React、TypeScript、Next.js、Node.js、PostgreSQL、Docker、Git
工作经历：
- 某科技公司前端工程师（2021-2024）
  使用 React + TypeScript 开发 SaaS 产品，负责核心组件库建设
  使用 Next.js 做 SSR 优化，页面加载速度提升 40%
  参与 Node.js 后端接口开发，独立交付过3个完整模块
教育：本科 计算机科学
""",
        "jd_text": """
职位：高级前端工程师
要求：
- 3年以上 React 开发经验（必须）
- 熟练掌握 TypeScript（必须）
- 有 Next.js SSR 经验（必须）
- 了解 Node.js 后端开发（加分）
- 有 Docker 使用经验（加分）
"""
    },
    {
        "name": "低匹配：Java后端 vs 前端岗位",
        "expected_score_range": (10, 40),
        "expected_matched": [],
        "expected_missing_contains": ["React", "TypeScript"],
        "resume_text": """
姓名：李四
技能：Java、Spring Boot、MySQL、Redis、Kafka、Maven
工作经历：
- 某银行软件开发工程师（2020-2024）
  使用 Spring Boot 开发微服务，负责支付模块
  优化 MySQL 查询性能，接口响应时间降低 50%
教育：本科 软件工程
""",
        "jd_text": """
职位：高级前端工程师
要求：
- 3年以上 React 开发经验（必须）
- 熟练掌握 TypeScript（必须）
- 有 Next.js SSR 经验（必须）
- CSS/Tailwind 样式能力（必须）
"""
    },
    {
        "name": "中等匹配：全栈 vs AI应用开发岗",
        "expected_score_range": (45, 75),
        "expected_matched": ["Python", "API"],
        "expected_missing_contains": ["LangChain"],
        "resume_text": """
姓名：王五
技能：Python、FastAPI、React、PostgreSQL、Docker、REST API
工作经历：
- 某创业公司全栈工程师（2022-2024）
  使用 FastAPI + React 构建 SaaS 产品
  设计并实现 RESTful API，对接多个第三方服务
  使用 PostgreSQL 做数据存储，熟悉基础 SQL 优化
教育：本科 信息工程
""",
        "jd_text": """
职位：AI应用开发工程师
要求：
- Python 开发经验（必须）
- LangChain / LangGraph 框架经验（必须）
- RAG 系统设计与实现（必须）
- 向量数据库使用经验（必须）
- FastAPI 开发经验（加分）
- React 前端能力（加分）
"""
    },
]