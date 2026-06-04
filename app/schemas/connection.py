from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# ── Request: create a connection ───────────────────────────────────────────────
class ConnectionCreate(BaseModel):
    connected_user_id: int


# ── Response schema ────────────────────────────────────────────────────────────
class Connection(BaseModel):
    id: int
    user_id: int
    connected_user_id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
