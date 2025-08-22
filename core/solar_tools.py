from datetime import datetime, timedelta
from .goodwe_client import client


def _parse_chart_energy(chart: dict) -> float:
    points = chart.get("chart", [])
    if not points:
        return 0.0
    day_kwh = 0.0
    prev_time = None
    for ts, power in points:
        t = datetime.fromisoformat(ts)
        if prev_time is not None:
            hours = (t - prev_time).total_seconds() / 3600.0
            day_kwh += power * hours / 1000.0
        prev_time = t
    return day_kwh


async def query_generation(start_date: str, end_date: str | None = None) -> dict:
    sd = datetime.fromisoformat(start_date).date()
    ed = datetime.fromisoformat(end_date).date() if end_date else sd
    total = 0.0
    current = sd
    while current <= ed:
        chart = await client.get_power_chart(datetime.combine(current, datetime.min.time()))
        total += _parse_chart_energy(chart)
        current += timedelta(days=1)
    return {"kwh": round(total, 2), "period": f"{start_date} to {end_date or start_date}"}


async def get_solar_stats() -> dict:
    today = datetime.now().date()
    daily_values = []
    for i in range(7):
        day = today - timedelta(days=i)
        chart = await client.get_power_chart(datetime.combine(day, datetime.min.time()))
        daily_values.append(_parse_chart_energy(chart))
    if not daily_values:
        return {"error": "No data available"}
    total_generation = sum(daily_values)
    avg_daily = total_generation / len(daily_values)
    max_daily = max(daily_values)
    min_daily = min(daily_values)
    return {
        "total_kwh": round(total_generation, 2),
        "average_daily_kwh": round(avg_daily, 2),
        "max_daily_kwh": round(max_daily, 2),
        "min_daily_kwh": round(min_daily, 2),
        "total_days": len(daily_values),
    }
