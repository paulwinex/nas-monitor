from datetime import datetime

from pydantic import BaseModel


class Metrics(BaseModel):
    device_name: str
    label: str
    value: float


class RequestMetricsPayload(BaseModel):
    range_name: str
    from_date: datetime|int
    to_date: datetime|int
