import os
import random
import zlib
from datetime import date, timedelta

import pandas as pd

MENU_ITEMS = [
    ("Burger", 9.99),
    ("Fries", 3.99),
    ("Soda", 2.50),
    ("Salad", 7.49),
    ("Pizza Slice", 4.99),
    ("Pasta", 11.99),
]

HOLIDAY_MONTH_DAY = {(1, 1), (12, 24), (12, 25), (2, 14), (11, 27)}


def _is_holiday(d: date) -> bool:
    return (d.month, d.day) in HOLIDAY_MONTH_DAY


def generate_branch_sales(
    branch_name: str,
    start_date: date,
    num_days: int,
    base_daily_revenue: float,
    seed: int = 0,
) -> pd.DataFrame:
    rng = random.Random(seed)
    rows = []

    for day_offset in range(num_days):
        current_date = start_date + timedelta(days=day_offset)
        is_weekend = current_date.weekday() >= 5
        multiplier = 1.0
        if is_weekend:
            multiplier *= 1.4
        if _is_holiday(current_date):
            multiplier *= 1.8

        target_revenue = base_daily_revenue * multiplier
        revenue_so_far = 0.0
        # Generate transactions until we roughly hit the day's target revenue.
        while revenue_so_far < target_revenue:
            item, price = rng.choice(MENU_ITEMS)
            quantity = rng.randint(1, 4)
            hour = rng.randint(10, 21)
            minute = rng.randint(0, 59)
            amount = round(price * quantity, 2)
            rows.append({
                "Date": f"{current_date.isoformat()} {hour:02d}:{minute:02d}",
                "Item": item,
                "Qty": quantity,
                "Total": amount,
            })
            revenue_so_far += amount

    return pd.DataFrame(rows, columns=["Date", "Item", "Qty", "Total"])


if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    branches = [
        ("Downtown", 1200.0),
        ("Uptown", 900.0),
        ("Riverside", 1500.0),
    ]
    start = date.today() - timedelta(days=365)

    for branch_name, base_revenue in branches:
        df = generate_branch_sales(branch_name, start, 365, base_revenue, seed=zlib.crc32(branch_name.encode()) % 1000)
        path = os.path.join(output_dir, f"{branch_name}.csv")
        df.to_csv(path, index=False)
        print(f"Wrote {len(df)} rows to {path}")
