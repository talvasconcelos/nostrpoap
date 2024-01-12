from typing import Optional
from pydantic import BaseModel
from abc import abstractmethod
from .nostr.event import NostrEvent
import json
import time
import secp256k1

######################################## NOSTR ########################################


class Nostrable:
    @abstractmethod
    def to_nostr_event(self, pubkey: str) -> NostrEvent:
        pass

    @abstractmethod
    def to_nostr_delete_event(self, pubkey: str) -> NostrEvent:
        pass


class CreateIssuer(BaseModel):
    private_key: str
    public_key: str
    meta: str = "{}"


class Issuer(BaseModel):
    id: str
    user_id: str
    private_key: str
    public_key: str
    meta: str

    def sign_hash(self, hash: bytes) -> str:
        privkey = secp256k1.PrivateKey(bytes.fromhex(self.private_key))
        sig = privkey.schnorr_sign(hash, None, raw=True)
        return sig.hex()


class CreatePOAP(BaseModel):
    id: Optional[str]
    name: str
    description: Optional[str]
    image: str
    thumbs: Optional[str]
    event_id: Optional[str]
    event_created_at: Optional[int]


class POAP(CreatePOAP, Nostrable):
    id: str
    issuer_id: str

    def to_nostr_event(self, public_key: str) -> NostrEvent:
        event = NostrEvent(
            pubkey=public_key,
            created_at=round(time.time()),
            kind=30009,
            tags=[
                ["d", self.id],
                ["name", self.name],
                ["description", self.description],
                ["image", self.image, "1024x1024"],
                ["thumb", self.thumbs, "256x256"] if self.thumbs else [],
            ],
            content="",
        )
        event.id = event.event_id

        return event


class CreateAward(BaseModel):
    id: Optional[str]
    badge_id: str
    issuer: str
    claim_pubkey: str
    event_id: Optional[str]
    event_created_at: Optional[int]


class Award(CreateAward, Nostrable):
    id: str

    def to_nostr_event(self, public_key: str) -> NostrEvent:
        event = NostrEvent(
            pubkey=public_key,
            created_at=round(time.time()),
            kind=8,
            tags=[
                ["a", f"30009:{self.badge_id}"],
                ["p", self.claim_pubkey],
            ],
            content="",
        )
        event.id = event.event_id

        return event
