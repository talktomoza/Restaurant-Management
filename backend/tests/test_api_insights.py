import json
from datetime import date, timedelta

from app.db.models import Forecast


def test_weekly_summary_endpoint_returns_insight(client, auth_headers, db_session, monkeypatch):
    response = client.post(
        "/branches", json={"name": "Downtown", "location": "Main St"}, headers=auth_headers
    )
    branch_id = response.json()["id"]

    for i in range(7):
        db_session.add(Forecast(
            branch_id=branch_id,
            date=date.today() + timedelta(days=i),
            predicted_revenue=1000.0,
            lower_bound=900.0,
            upper_bound=1100.0,
        ))
    db_session.commit()

    def fake_call(system_prompt, user_content):
        return json.dumps({"summary": "All good.", "key_risks": [], "recommendations": []})

    monkeypatch.setattr(
        "app.api.routes_insights.call_openrouter_chat", fake_call
    )

    response = client.post(
        f"/branches/{branch_id}/insights/weekly-summary", headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == "All good."
