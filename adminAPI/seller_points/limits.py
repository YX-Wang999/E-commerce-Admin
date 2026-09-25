"""Platform guardrails for seller points rules."""

from decimal import Decimal

MAX_EARN_RATE = Decimal('10.00')
MIN_REDEEM_RATE = Decimal('100.00')
MAX_REDEEM_RATE = Decimal('1000.00')
MIN_EXPIRE_DAYS = 30
MAX_REDEEM_PERCENT = Decimal('50.00')

DEFAULT_EARN_RATE = Decimal('1.00')
DEFAULT_REDEEM_RATE = Decimal('100.00')
DEFAULT_MAX_REDEEM_PERCENT = Decimal('30.00')
DEFAULT_EXPIRE_DAYS = 365
DEFAULT_MAX_EARN_PER_ORDER = 1000
