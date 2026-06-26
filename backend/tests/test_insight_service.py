import json
from datetime import date, datetime, timedelta

from app.db.models import Branch, Forecast, AiInsight
from app.services.insight_service import generate_weekly_insight, InsightContent


def _seed_forecast(db_session, branch_id):
    for i in range(7):
        db_session.add(Forecast(
            branch_id=branch_id,
            date=date.today() + timedelta(days=i),
            predicted_revenue=1000.0 + i * 10,
            lower_bound=900.0,
            upper_bound=1100.0,
        ))
    db_session.commit()


def test_generate_weekly_insight_uses_llm_response(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_forecast(db_session, branch.id)

    def fake_llm_call(system_prompt, user_content):
        return json.dumps({
            "summary": "Revenue trending up this week.",
            "key_risks": ["No major risks detected."],
            "recommendations": ["Maintain current staffing levels."],
        })

    result = generate_weekly_insight(db_session, branch.id, llm_call=fake_llm_call)

    assert isinstance(result, InsightContent)
    assert result.summary == "Revenue trending up this week."
    insight_row = db_session.query(AiInsight).filter(AiInsight.type == "weekly_summary").one()
    assert insight_row.branch_id == branch.id


def test_generate_weekly_insight_falls_back_on_malformed_llm_output(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_forecast(db_session, branch.id)

    def broken_llm_call(system_prompt, user_content):
        return "not json at all"

    result = generate_weekly_insight(db_session, branch.id, llm_call=broken_llm_call)

    assert isinstance(result, InsightContent)
    assert result.summary != ""


def test_generate_weekly_insight_uses_cache_within_rate_limit_window(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_forecast(db_session, branch.id)

    db_session.add(AiInsight(
        branch_id=branch.id,
        type="weekly_summary",
        content=json.dumps({
            "summary": "Cached summary.",
            "key_risks": [],
            "recommendations": [],
        }),
        generated_at=datetime.utcnow(),
    ))
    db_session.commit()

    call_count = {"n": 0}

    def counting_llm_call(system_prompt, user_content):
        call_count["n"] += 1
        return json.dumps({"summary": "fresh", "key_risks": [], "recommendations": []})

    result = generate_weekly_insight(db_session, branch.id, llm_call=counting_llm_call)

    assert result.summary == "Cached summary."
    assert call_count["n"] == 0
