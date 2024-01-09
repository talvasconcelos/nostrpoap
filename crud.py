from typing import List, Optional
from lnbits.helpers import urlsafe_short_hash
import uuid

from . import db
from .models import CreateIssuer, Issuer, POAP, CreatePOAP
from loguru import logger


async def get_issuer_by_pubkey(pubkey: str) -> Optional[Issuer]:
    row = await db.fetchone(
        "SELECT * FROM poap.issuers WHERE public_key = ?", (pubkey,)
    )
    return Issuer(**row) if row else None


async def get_issuer_for_user(user_id: str) -> Optional[Issuer]:
    row = await db.fetchone("SELECT * FROM poap.issuers WHERE user_id = ?", (user_id,))
    return Issuer(**row) if row else None


async def create_issuer(user_id: str, data: CreateIssuer) -> Issuer:
    issuer_id = urlsafe_short_hash()
    await db.execute(
        """
        INSERT INTO poap.issuers (id, user_id, private_key, public_key, meta)
        VALUES (?, ?, ?, ?, ?)
        """,
        (issuer_id, user_id, data.private_key, data.public_key, data.meta),
    )
    issuer = await get_issuer(issuer_id)
    assert issuer, "Newly created issuer couldn't be retrieved"
    return issuer


async def get_issuer(issuer_id: str) -> Optional[Issuer]:
    row = await db.fetchone("SELECT * FROM poap.issuers WHERE id = ?", (issuer_id,))
    return Issuer(**row) if row else None


async def create_poap(issuer_id: str, data: CreatePOAP) -> POAP:
    badge_id = uuid.uuid4().hex
    await db.execute(
        """
        INSERT INTO poap.badges (id, issuer_id, name, description, image, thumbs)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            badge_id,
            issuer_id,
            data.name,
            data.description,
            data.image,
            data.thumbs,
        ),
    )
    poap = await get_poap(badge_id)
    assert poap, "Newly created poap couldn't be retrieved"
    return poap


async def get_poap(badge_id: str) -> Optional[POAP]:
    row = await db.fetchone("SELECT * FROM poap.badges WHERE id = ?", (badge_id,))
    return POAP(**row) if row else None


async def get_poaps(issuer_id: str) -> List[POAP]:
    rows = await db.fetchall(
        "SELECT * FROM poap.badges WHERE issuer_id = ?", (issuer_id,)
    )
    return [POAP(**row) for row in rows]
