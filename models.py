from typing import Optional
from pydantic import BaseModel


class CreateIssuer(BaseModel):
    private_key: str
    public_key: str
    meta: str = "{}"


class Issuer(BaseModel):
    id: str
    private_key: str
    public_key: str
    meta: str


class CreatePOAP(BaseModel):
    issuer_id: str
    name: str
    description: Optional[str]
    image: str
    thumbs: Optional[str]


class POAP(BaseModel):
    id: str
    issuer_id: str
    name: str
    description: Optional[str]
    image: str
    thumbs: str


class CreateAward(BaseModel):
    poap_id: str
    issuer: str
    claim_pubkey: str


class Award(BaseModel):
    id: str
    poap_id: str
    issuer: str
    claim_pubkey: str
    time: str