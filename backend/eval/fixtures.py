TEST_CASES = [
    {
        "name": "High match: React frontend resume vs frontend role",
        "expected_score_range": (70, 95),
        "expected_matched": ["React", "TypeScript"],
        "expected_missing_not_contains": ["React"],  # High-match cases should not miss React.
        "resume_text": """
Name: Alex Chen
Skills: React, TypeScript, Next.js, Node.js, PostgreSQL, Docker, Git
Work Experience:
- Frontend Engineer at a technology company (2021-2024)
  Built SaaS product features with React and TypeScript, including a shared component library
  Improved page load speed by 40% through Next.js SSR optimization
  Contributed to Node.js backend APIs and independently delivered three full modules
Education: B.S. in Computer Science
""",
        "jd_text": """
Title: Senior Frontend Engineer
Requirements:
- 3+ years of React experience (required)
- Strong TypeScript proficiency (required)
- Next.js SSR experience (required)
- Node.js backend development knowledge (nice to have)
- Docker experience (nice to have)
"""
    },
    {
        "name": "Low match: Java backend resume vs frontend role",
        "expected_score_range": (10, 40),
        "expected_matched": [],
        "expected_missing_contains": ["React", "TypeScript"],
        "resume_text": """
Name: Ben Li
Skills: Java, Spring Boot, MySQL, Redis, Kafka, Maven
Work Experience:
- Software Engineer at a banking software company (2020-2024)
  Built payment microservices with Spring Boot
  Optimized MySQL queries and reduced API response time by 50%
Education: B.S. in Software Engineering
""",
        "jd_text": """
Title: Senior Frontend Engineer
Requirements:
- 3+ years of React experience (required)
- Strong TypeScript proficiency (required)
- Next.js SSR experience (required)
- CSS and Tailwind styling ability (required)
"""
    },
    {
        "name": "Medium match: full-stack resume vs AI application role",
        "expected_score_range": (45, 75),
        "expected_matched": ["Python", "API"],
        "expected_missing_contains": ["LangChain"],
        "resume_text": """
Name: Chris Wang
Skills: Python, FastAPI, React, PostgreSQL, Docker, REST API
Work Experience:
- Full-Stack Engineer at a startup (2022-2024)
  Built SaaS product features with FastAPI and React
  Designed and implemented RESTful APIs that integrated with multiple third-party services
  Used PostgreSQL for data storage and handled basic SQL optimization
Education: B.S. in Information Engineering
""",
        "jd_text": """
Title: AI Application Engineer
Requirements:
- Python development experience (required)
- LangChain / LangGraph framework experience (required)
- RAG system design and implementation (required)
- Vector database experience (required)
- FastAPI development experience (nice to have)
- React frontend ability (nice to have)
"""
    },
]
