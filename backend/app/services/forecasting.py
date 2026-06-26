from datetime import date, datetime, timedelta
import logging
import warnings

import pandas as pd
from prophet import Prophet
from sqlalchemy.orm import Session

from app.db.models import SalesTransaction, Forecast
from app.schemas.forecast import ForecastPoint

# Suppress Prophet logging and warnings
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
warnings.filterwarnings("ignore", category=DeprecationWarning)

MIN_HISTORY_DAYS = 14
MIN_EVAL_HISTORY_DAYS = 28
EVAL_HOLDOUT_DAYS = 14


def _daily_revenue_df(db: Session, branch_id: int) -> pd.DataFrame:
    rows = (
        db.query(SalesTransaction)
        .filter(SalesTransaction.branch_id == branch_id)
        .all()
    )
    df = pd.DataFrame([{"ds": r.timestamp.date(), "y": r.amount} for r in rows])
    if df.empty:
        return df
    daily = df.groupby("ds", as_index=False)["y"].sum()
    daily["ds"] = pd.to_datetime(daily["ds"])
    return daily.sort_values("ds")


def generate_forecast(db: Session, branch_id: int, horizon_days: int) -> list[ForecastPoint]:
    daily = _daily_revenue_df(db, branch_id)
    if len(daily) < MIN_HISTORY_DAYS:
        raise ValueError(
            f"Need at least {MIN_HISTORY_DAYS} days of history, found {len(daily)}"
        )

    model = Prophet(
        weekly_seasonality=True,
        daily_seasonality=False,
        interval_width=0.95
    )
    model.fit(daily)

    future = model.make_future_dataframe(periods=horizon_days)
    forecast = model.predict(future)
    forecast_tail = forecast.tail(horizon_days)

    today = date.today()
    db.query(Forecast).filter(
        Forecast.branch_id == branch_id, Forecast.date >= today
    ).delete()

    points = []
    for _, row in forecast_tail.iterrows():
        point_date = row["ds"].date()
        point = ForecastPoint(
            date=point_date,
            predicted_revenue=max(0.0, float(row["yhat"])),
            lower_bound=max(0.0, float(row["yhat_lower"])),
            upper_bound=max(0.0, float(row["yhat_upper"])),
        )
        points.append(point)
        db.add(Forecast(
            branch_id=branch_id,
            date=point.date,
            predicted_revenue=point.predicted_revenue,
            lower_bound=point.lower_bound,
            upper_bound=point.upper_bound,
            generated_at=datetime.utcnow(),
        ))

    db.commit()
    return points


def evaluate_forecast_accuracy(db: Session, branch_id: int) -> dict:
    daily = _daily_revenue_df(db, branch_id)
    if len(daily) < MIN_EVAL_HISTORY_DAYS:
        return {"mae_pct": None, "rmse_pct": None}

    train = daily.iloc[:-EVAL_HOLDOUT_DAYS]
    holdout = daily.iloc[-EVAL_HOLDOUT_DAYS:]

    model = Prophet(
        weekly_seasonality=True,
        daily_seasonality=False,
        interval_width=0.95
    )
    model.fit(train)

    future = model.make_future_dataframe(periods=EVAL_HOLDOUT_DAYS)
    forecast = model.predict(future)
    predicted = forecast.tail(EVAL_HOLDOUT_DAYS)["yhat"].to_numpy()
    actual = holdout["y"].to_numpy()

    errors = predicted - actual
    mae = abs(errors).mean()
    rmse = (errors ** 2).mean() ** 0.5
    mean_actual = actual.mean() if actual.mean() != 0 else 1.0

    return {
        "mae_pct": round(float(mae / mean_actual * 100), 2),
        "rmse_pct": round(float(rmse / mean_actual * 100), 2),
    }
