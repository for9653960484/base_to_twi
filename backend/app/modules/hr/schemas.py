from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class HRSyncRequest(BaseModel):
    sync_type: str = "incremental"  # full | incremental


class HRSyncStatus(BaseModel):
    last_sync_at: Optional[datetime] = None
    status: Optional[str] = None
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
