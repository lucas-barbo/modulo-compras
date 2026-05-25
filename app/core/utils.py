from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from math import ceil


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def isoformat_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def isoformat_date(value: date | None) -> str | None:
    return value.isoformat() if value else None


def build_order_number(order_id: int) -> str:
    return f"OC-{order_id:06d}"


def compute_pages(total: int, size: int) -> int:
    if total == 0:
        return 0
    return ceil(total / size)


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
