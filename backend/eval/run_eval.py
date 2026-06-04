import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import app
from fixtures import TEST_CASES
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

judge_model = ChatAnthropic(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL"),
    model=os.getenv("MODEL_NAME"),
)

def check_score_in_range(score, expected_range):
    low, high = expected_range
    passed = low <= score <= high
    return passed, f"得分 {score}，期望范围 [{low}, {high}]"

def check_skills(actual_skills, expected_contains):
    if not expected_contains:
        return True, "无要求"
    matched = [s for s in expected_contains if any(s.lower() in skill.lower() for skill in actual_skills)]
    passed = len(matched) == len(expected_contains)
    return passed, f"期望包含 {expected_contains}，实际: {actual_skills}"

def llm_judge_suggestions(suggestions, resume_text, jd_text, score):
    response = judge_model.invoke([
        SystemMessage("""你是一个简历优化建议评审专家。
评估优化建议的质量，返回 JSON：
{
  "score": 1-5,
  "is_actionable": true/false,
  "is_specific": true/false,
  "comment": "简短评价"
}
评分标准：5=非常具体可执行，3=中等，1=太泛泛无意义
只返回 JSON。"""),
        HumanMessage(f"""简历摘要：{resume_text[:300]}
JD摘要：{jd_text[:300]}
匹配得分：{score}
优化建议：{suggestions}""")
    ])
    try:
        return json.loads(response.content)
    except Exception:
        return {"score": 0, "comment": "解析失败", "is_actionable": False, "is_specific": False}

def run_eval():
    results = []
    print("\n" + "="*60)
    print("Resume Analyzer — Evaluation Report")
    print("="*60)

    for case in TEST_CASES:
        print(f"\n▶ 测试用例：{case['name']}")

        # 调用 pipeline
        state = app.invoke({
            "resume_text": case["resume_text"],
            "jd_text": case["jd_text"],
            "messages": [],
            "rag_context": "",
            "jd_requirements": "",
            "jd_must_skills": [],
            "jd_nice_skills": [],
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "suggestions": "",
            "rewritten_resume": "",
            "error": "",
        })

        checks = []

        # 1. 分数范围检查
        passed, msg = check_score_in_range(state["match_score"], case["expected_score_range"])
        checks.append(("分数范围", passed, msg))
        print(f"  {'✓' if passed else '✗'} 分数范围: {msg}")

        # 2. 应匹配的技能
        if case.get("expected_matched"):
            passed, msg = check_skills(state["matched_skills"], case["expected_matched"])
            checks.append(("匹配技能", passed, msg))
            print(f"  {'✓' if passed else '✗'} 匹配技能: {msg}")

        # 3. 应缺失的技能
        if case.get("expected_missing_contains"):
            passed, msg = check_skills(state["missing_skills"], case["expected_missing_contains"])
            checks.append(("缺失技能", passed, msg))
            print(f"  {'✓' if passed else '✗'} 缺失技能识别: {msg}")

        # 4. LLM-as-Judge 评价建议质量
        judge_result = llm_judge_suggestions(
            state["suggestions"], case["resume_text"], case["jd_text"], state["match_score"]
        )
        judge_passed = judge_result["score"] >= 3
        checks.append(("建议质量", judge_passed, f"LLM评分 {judge_result['score']}/5 — {judge_result['comment']}"))
        print(f"  {'✓' if judge_passed else '✗'} 建议质量: LLM评分 {judge_result['score']}/5 — {judge_result['comment']}")

        case_passed = all(c[1] for c in checks)
        results.append((case["name"], case_passed, checks))

    # 汇总
    print("\n" + "="*60)
    passed_count = sum(1 for _, p, _ in results if p)
    print(f"总结: {passed_count}/{len(results)} 用例通过")
    for name, passed, _ in results:
        print(f"  {'✓' if passed else '✗'} {name}")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_eval()