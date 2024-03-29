# generated by datamodel-codegen:
#   filename:  offer.json

from __future__ import annotations

from pydantic import BaseModel
from pydantic import Extra


class Gentk(BaseModel):
    class Config:
        extra = Extra.forbid

    id: str
    version: str


class OfferParameter(BaseModel):
    class Config:
        extra = Extra.forbid

    gentk: Gentk
    price: str
