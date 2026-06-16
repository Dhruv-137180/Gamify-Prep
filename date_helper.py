"""
Single source of truth for 'today'.  Dev Mode overrides this; all other code calls get_today().
"""
from datetime import date, timedelta
from typing import Optional

_simulated_date: Optional[date] = None


def get_today() -> date:
    return _simulated_date if _simulated_date is not None else date.today()


def get_today_str() -> str:
    return get_today().isoformat()


def set_simulated_date(d: date) -> None:
    global _simulated_date
    _simulated_date = d


def advance_day() -> None:
    global _simulated_date
    _simulated_date = get_today() + timedelta(days=1)


def clear_simulated_date() -> None:
    global _simulated_date
    _simulated_date = None


def is_simulated() -> bool:
    return _simulated_date is not None
