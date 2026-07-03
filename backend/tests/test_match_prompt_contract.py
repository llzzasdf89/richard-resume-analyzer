from pathlib import Path


def test_match_analysis_prompt_requires_jd_relevant_matched_skills():
    graph_source = Path("graph.py").read_text()

    assert "directly relevant to the current job description" in graph_source
    assert "Do not include resume-only skills" in graph_source
    assert "do not include React" in graph_source
