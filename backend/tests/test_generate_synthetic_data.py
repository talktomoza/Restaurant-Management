from datetime import date

from scripts.generate_synthetic_data import generate_branch_sales


def test_generate_branch_sales_shape_and_columns():
    df = generate_branch_sales(
        branch_name="Downtown",
        start_date=date(2026, 1, 1),
        num_days=30,
        base_daily_revenue=1000.0,
        seed=42,
    )
    assert list(df.columns) == ["Date", "Item", "Qty", "Total"]
    assert len(df) > 0
    assert (df["Qty"] > 0).all()
    assert (df["Total"] > 0).all()


def test_generate_branch_sales_is_deterministic_with_seed():
    df1 = generate_branch_sales("Downtown", date(2026, 1, 1), 30, 1000.0, seed=7)
    df2 = generate_branch_sales("Downtown", date(2026, 1, 1), 30, 1000.0, seed=7)
    assert df1["Total"].sum() == df2["Total"].sum()


def test_weekend_revenue_exceeds_weekday_on_average():
    df = generate_branch_sales("Downtown", date(2026, 1, 1), 90, 1000.0, seed=1)
    df["Date"] = df["Date"].astype("datetime64[ns]")
    df["dow"] = df["Date"].dt.dayofweek
    weekday_avg = df[df["dow"] < 5].groupby(df["Date"].dt.date)["Total"].sum().mean()
    weekend_avg = df[df["dow"] >= 5].groupby(df["Date"].dt.date)["Total"].sum().mean()
    assert weekend_avg > weekday_avg
