from typing import List, Optional
from lnbits.helpers import urlsafe_short_hash
import uuid

from . import db
from .models import CreateIssuer, Issuer, POAP, CreatePOAP, CreateAward, Award
from loguru import logger

######################################## ISSUER ########################################


async def get_issuer_by_pubkey(pubkey: str) -> Optional[Issuer]:
    row = await db.fetchone(
        "SELECT * FROM poap.issuers WHERE public_key = ?", (pubkey,)
    )
    return Issuer(**row) if row else None


async def get_issuer_for_user(user_id: str) -> Optional[Issuer]:
    row = await db.fetchone("SELECT * FROM poap.issuers WHERE user_id = ?", (user_id,))
    return Issuer(**row) if row else None


async def get_issuers_ids_with_pubkeys() -> List[str]:
    rows = await db.fetchall(
        """SELECT id, public_key FROM poap.issuers""",
    )

    return [(row[0], row[1]) for row in rows]


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


async def delete_issuer_poaps(issuer_id: str) -> None:
    await db.execute(
        """
        DELETE FROM poap.badges WHERE issuer_id = ?
        """,
        (issuer_id,),
    )


async def delete_issuer_awards(issuer_id: str) -> None:
    await db.execute(
        """
        DELETE FROM poap.awards WHERE issuer = ?
        """,
        (issuer_id,),
    )


async def delete_issuer(issuer_id: str) -> None:
    await db.execute(
        """
        DELETE FROM poap.issuers WHERE id = ?
        """,
        (issuer_id,),
    )


######################################## POAP ########################################


async def create_poap(issuer_id: str, data: CreatePOAP) -> POAP:
    logger.debug(f"Creating poap for issuer {issuer_id}, data: {data}")
    badge_id = data.id or uuid.uuid4().hex
    await db.execute(
        """
        INSERT INTO poap.badges (id, issuer_id, name, description, image, thumbs, event_id, event_created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            badge_id,
            issuer_id,
            data.name,
            data.description,
            data.image,
            data.thumbs,
            data.event_id,
            data.event_created_at,
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


async def update_poap(issuer_id: str, data: POAP) -> Optional[POAP]:
    await db.execute(
        """
        UPDATE poap.badges SET name = ?, description = ?, image = ?, thumbs = ?, event_id = ?, event_created_at = ?
        WHERE issuer_id = ? AND id = ?
        """,
        (
            data.name,
            data.description,
            data.image,
            data.thumbs,
            data.event_id,
            data.event_created_at,
            issuer_id,
            data.id,
        ),
    )
    return await get_poap(data.id)


async def delete_poap(issuer_id: str, badge_id: str) -> None:
    await db.execute(
        """
        DELETE FROM poap.badges WHERE issuer_id = ? AND id = ?
        """,
        (issuer_id, badge_id),
    )


async def get_last_poap_update_time() -> int:
    row = await db.fetchone(
        """
            SELECT event_created_at FROM poap.badges 
            ORDER BY event_created_at DESC LIMIT 1
        """,
        (),
    )
    return row[0] or 0 if row else 0


######################################## AWARD ########################################


async def create_award_poap(issuer_id: str, data: CreateAward) -> Award:
    award_id = data.id or uuid.uuid4().hex
    await db.execute(
        """
        INSERT INTO poap.awards (id, badge_id, issuer, claim_pubkey, event_id, event_created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            award_id,
            data.badge_id,
            issuer_id,
            data.claim_pubkey,
            data.event_id,
            data.event_created_at,
        ),
    )
    award = await get_award_poap(award_id)
    assert award, "Newly created award couldn't be retrieved"
    return award


async def check_awarded_to_pubkey(badge_id: str, pubkey: str):
    # check if the badge as been awarded to pubkey
    count = await db.fetchone(
        "SELECT COUNT(1) FROM poap.awards WHERE badge_id = ? AND claim_pubkey = ?",
        (
            badge_id,
            pubkey,
        ),
    )
    exists = int(count[0])
    return not exists


async def get_award_poap(award_id: str) -> Optional[Award]:
    row = await db.fetchone("SELECT * FROM poap.awards WHERE id = ?", (award_id,))
    return Award(**row) if row else None


async def get_awards_poap(badge_id: str) -> List[Award]:
    rows = await db.fetchall(
        "SELECT * FROM poap.awards WHERE badge_id = ?", (badge_id,)
    )
    return [Award(**row) for row in rows]


async def get_awards(issuer: str) -> List[Award]:
    rows = await db.fetchall("SELECT * FROM poap.awards WHERE issuer = ?", (issuer,))
    return [Award(**row) for row in rows]


async def get_last_award_update_time() -> int:
    row = await db.fetchone(
        """
            SELECT event_created_at FROM poap.awards 
            ORDER BY event_created_at DESC LIMIT 1
        """,
        (),
    )
    return row[0] or 0 if row else 0


async def update_award(award_id: str, data: CreateAward) -> Award:
    await db.execute(
        """
        UPDATE poap.awards SET badge_id = ?, issuer = ?, claim_pubkey = ?, event_id = ?, event_created_at = ?
        WHERE id = ?
        """,
        (
            data.badge_id,
            data.issuer,
            data.claim_pubkey,
            data.event_id,
            data.event_created_at,
            award_id,
        ),
    )
    return await get_award_poap(award_id)
