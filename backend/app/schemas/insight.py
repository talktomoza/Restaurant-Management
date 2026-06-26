from pydantic import BaseModel


class InsightContent(BaseModel):
    summary: str
    key_risks: list[str]
    recommendations: list[str]
