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
    return passed, f"score {score}, expected range [{low}, {high}]"

def check_skills(actual_skills, expected_contains):
    if not expected_contains:
        return True, "no requirement"
    matched = [s for s in expected_contains if any(s.lower() in skill.lower() for skill in actual_skills)]
    passed = len(matched) == len(expected_contains)
    return passed, f"expected {expected_contains}, actual: {actual_skills}"

def llm_judge_suggestions(suggestions, resume_text, jd_text, score):
    response = judge_model.invoke([
        SystemMessage("""You are a resume optimization suggestion reviewer.
Evaluate the quality of the optimization suggestions and return JSON:
{
  "score": 1-5,
  "is_actionable": true/false,
  "is_specific": true/false,
  "comment": "brief review"
}
Scoring guide: 5=very specific and actionable, 3=moderate, 1=too generic.
Return JSON only."""),
        HumanMessage(f"""Resume summary: {resume_text[:300]}
Job description summary: {jd_text[:300]}
Match score: {score}
Optimization suggestions: {suggestions}""")
    ])
    try:
        return json.loads(response.content)
    except Exception:
        return {"score": 0, "comment": "Parse failed", "is_actionable": False, "is_specific": False}

def run_eval():
    results = []
    print("\n" + "="*60)
    print("Resume Analyzer — Evaluation Report")
    print("="*60)

    for case in TEST_CASES:
        print(f"\n▶ Test case: {case['name']}")

        # Invoke the pipeline.
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

        # 1. Score range check.
        passed, msg = check_score_in_range(state["match_score"], case["expected_score_range"])
        checks.append(("score range", passed, msg))
        print(f"  {'✓' if passed else '✗'} Score range: {msg}")

        # 2. Expected matched skills.
        if case.get("expected_matched"):
            passed, msg = check_skills(state["matched_skills"], case["expected_matched"])
            checks.append(("matched skills", passed, msg))
            print(f"  {'✓' if passed else '✗'} Matched skills: {msg}")

        # 3. Expected missing skills.
        if case.get("expected_missing_contains"):
            passed, msg = check_skills(state["missing_skills"], case["expected_missing_contains"])
            checks.append(("missing skills", passed, msg))
            print(f"  {'✓' if passed else '✗'} Missing skill detection: {msg}")

        # 4. LLM-as-judge suggestion quality check.
        judge_result = llm_judge_suggestions(
            state["suggestions"], case["resume_text"], case["jd_text"], state["match_score"]
        )
        judge_passed = judge_result["score"] >= 3
        checks.append(("suggestion quality", judge_passed, f"LLM score {judge_result['score']}/5 — {judge_result['comment']}"))
        print(f"  {'✓' if judge_passed else '✗'} Suggestion quality: LLM score {judge_result['score']}/5 — {judge_result['comment']}")

        case_passed = all(c[1] for c in checks)
        results.append((case["name"], case_passed, checks))

    # Summary.
    print("\n" + "="*60)
    passed_count = sum(1 for _, p, _ in results if p)
    print(f"Summary: {passed_count}/{len(results)} cases passed")
    for name, passed, _ in results:
        print(f"  {'✓' if passed else '✗'} {name}")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_eval()
