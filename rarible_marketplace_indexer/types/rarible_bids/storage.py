# generated by datamodel-codegen:
#   filename:  storage.json

from __future__ import annotations

from typing import Dict
from typing import Optional

from pydantic import BaseModel
from pydantic import Extra


class RaribleBidsStorage(BaseModel):
    class Config:
        extra = Extra.forbid

    owner: str
    protocol_fee: str
    transfer_manager: str
    bids_storage: str
    default_bid_duration: int
    owner_candidate: Optional[str]
    max_bundle_items: str
    metadata: Dict[str, str]
