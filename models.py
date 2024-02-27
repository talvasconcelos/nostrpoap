from typing import Optional
from pydantic import BaseModel
from abc import abstractmethod
from .nostr.event import NostrEvent
import json
import time
import secp256k1
from enum import Enum
from .helpers import get_shared_secret, decrypt_message

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

    def decrypt_message(self, encrypted_message: str, public_key: str) -> str:
        encryption_key = get_shared_secret(self.private_key, public_key)
        return decrypt_message(encrypted_message, encryption_key)


class CreatePOAP(BaseModel):
    id: Optional[str]
    name: str
    description: Optional[str]
    image: str
    thumbs: Optional[str]
    event_id: Optional[str]
    event_created_at: Optional[int]
    geohash: Optional[str]


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
                ["subject", f"poap:{'location' if self.geohash else ''}"],
                ["alt", "Claim this POAP at https://poap.nostr.com"],
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
                ["a", f"30009:{public_key}:{self.badge_id}"],
                ["p", self.claim_pubkey],
                ["subject", "poap"],
            ],
            content="",
        )
        event.id = event.event_id

        return event
