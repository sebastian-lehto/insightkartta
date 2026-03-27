def trend_insight(trend: float, metric_name: str) -> str:
    if trend > 0:
        return f"{metric_name} has increased over time."
    elif trend < 0:
        return f"{metric_name} has decreased over time."
    return f"{metric_name} has remained stable."


def peak_insight(year: int, value: float, metric_name: str) -> str:
    return f"{metric_name} peaked in {year} at {value:.2f}."