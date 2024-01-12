import asyncio
import json
from typing import List, Optional, Tuple

from loguru import logger

from lnbits.bolt11 import decode
from lnbits.core.services import websocketUpdater, create_invoice, get_wallet

from . import nostr_client

from .crud import (
    get_issuers_ids_with_pubkeys,
    get_issuer_by_pubkey,
    create_poap,
    create_award_poap,
    get_last_award_update_time,
    get_last_poap_update_time,
)

from .nostr.event import NostrEvent
from .models import Nostrable, Issuer, POAP, CreateAward


async def sign_and_send_to_nostr(
    issuer: Issuer, n: Nostrable, delete=False
) -> NostrEvent:
    event = (
        n.to_nostr_delete_event(issuer.public_key)
        if delete
        else n.to_nostr_event(issuer.public_key)
    )
    event.sig = issuer.sign_hash(bytes.fromhex(event.id))
    await nostr_client.publish_nostr_event(event)

    return event


async def resubscribe_to_all_issuers():
    await nostr_client.unsubscribe_issuers()
    # give some time for the message to propagate
    await asyncio.sleep(1)
    await subscribe_to_all_issuers()


async def subscribe_to_all_issuers():
    ids = await get_issuers_ids_with_pubkeys()
    public_keys = [pk for _, pk in ids]

    last_poap_time = await get_last_poap_update_time()
    last_award_time = await get_last_award_update_time()

    logger.debug(f"Timestamps: {last_poap_time}, {last_award_time}")

    await nostr_client.subscribe_issuers(public_keys, last_poap_time, last_award_time)


async def process_nostr_message(msg: str):
    try:
        type, *rest = json.loads(msg)

        if type.upper() == "EVENT":
            _, event = rest
            event = NostrEvent(**event)
            if event.kind == 0:
                # await _handle_customer_profile_update(event)
                pass
            elif event.kind == 30009:
                await _handle_badge(event)
            elif event.kind == 8:
                await _handle_award(event)
            return

    except Exception as ex:
        logger.debug(ex)


async def _handle_badge(event: NostrEvent):
    try:
        issuer = await get_issuer_by_pubkey(event.pubkey)
        assert issuer, f"Issuer not found for public key '{event.pubkey}'"
        d = event.tag_values("d")
        name = event.tag_values("name")
        description = event.tag_values("description")
        image = event.tag_values("image")
        thumb = event.tag_values("thumb")

        if not d[0] or not image[0]:
            return

        poap = POAP(
            id=d[0],
            issuer_id=issuer.id,
            name=name[0] if len(name) else "Imported POAP",
            description=description[0],
            image=image[0],
            thumb=thumb[0],
            event_id=event.id,
            event_created_at=event.created_at,
        )
        await create_poap(issuer.id, poap)

    except Exception as ex:
        logger.error(ex)


async def _handle_award(event: NostrEvent):
    try:
        issuer = await get_issuer_by_pubkey(event.pubkey)
        assert issuer, f"Issuer not found for public key '{event.pubkey}'"

        badge = event.tag_values("a")
        assert badge, f"'a' tag not found on event"

        claim_pubkey = event.tag_values("p")
        assert claim_pubkey[0], f"'p' tag not found on event"

        award = CreateAward(
            badge_id=badge[0].split(":")[1],
            issuer=issuer.id,
            claim_pubkey=claim_pubkey[0],
            event_id=event.id,
            event_created_at=event.created_at,
        )
        await create_award_poap(issuer.id, award)

    except Exception as ex:
        logger.error(ex)
