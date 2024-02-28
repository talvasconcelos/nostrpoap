import asyncio
import json
from math import dist
from typing import List, Optional, Tuple
from webbrowser import get

from loguru import logger

from lnbits.bolt11 import decode
from lnbits.core.services import websocketUpdater, create_invoice, get_wallet
from .geohash.distances import geohash_approximate_distance, geohash_haversine_distance
from .geohash.geohash import gh_encode

from . import nostr_client

from .crud import (
    get_issuers_ids_with_pubkeys,
    get_issuer_by_pubkey,
    create_poap,
    create_award_poap,
    get_poaps,
    get_poap,
    get_awards,
    get_last_award_update_time,
    get_last_poap_update_time,
    update_poap,
    update_award,
    check_awarded_to_pubkey,
)

from .nostr.event import NostrEvent
from .models import Nostrable, Issuer, POAP, CreateAward


async def update_issuer_to_nostr(issuer: Issuer, delete_issuer=False) -> Issuer:
    # update poaps
    poaps = await get_poaps(issuer.id)
    for poap in poaps:
        event = await sign_and_send_to_nostr(issuer, poap)
        poap.event_id = event.id
        poap.event_created_at = event.created_at
        await update_poap(issuer.id, poap)

    if delete_issuer:
        # merchant profile updates not supported yet
        event = await sign_and_send_to_nostr(issuer, issuer, delete=True)

    return issuer


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
    last_dm_time = last_award_time

    logger.debug(f"Timestamps: {last_poap_time}, {last_award_time}")

    await nostr_client.subscribe_issuers(
        public_keys, last_poap_time, last_award_time, last_dm_time
    )


async def process_nostr_message(msg: str):
    try:
        type, *rest = json.loads(msg)

        if type.upper() == "EVENT":
            _, event = rest
            event = NostrEvent(**event)
            if event.kind == 4:
                await _handle_nip04_message(event)
            elif event.kind == 30009:
                await _handle_badge(event)
            elif event.kind == 8:
                await _handle_award(event)
            return

    except Exception as ex:
        logger.debug(ex)


async def _handle_nip04_message(event: NostrEvent):
    p_tags = event.tag_values("p")
    issuer_public_key = p_tags[0] if len(p_tags) else None
    issuer = (
        await get_issuer_by_pubkey(issuer_public_key) if issuer_public_key else None
    )

    assert issuer, f"Issuer not found for public key '{issuer_public_key}'"
    logger.debug(f"Handling NIP04 event: '{event.id}'")

    if issuer_public_key and event.has_tag_value("p", issuer_public_key):
        clear_text_msg = issuer.decrypt_message(event.content, event.pubkey)
        logger.debug(f"Clear text message: {clear_text_msg}")
        await _handle_incoming_dms(event, issuer, clear_text_msg)
    else:
        logger.warning(f"Bad NIP04 event: '{event.id}'")


async def _handle_incoming_dms(event: NostrEvent, issuer: Issuer, clear_text_msg: str):
    try:
        json_data = json.loads(clear_text_msg)
        if json_data and json_data["type"] == "claim_poap":
            logger.debug(f"Data: {json_data}")
            badge = await get_poap(json_data["badge_id"])
            assert badge, f"POAP not found!"
            not_yet_awarded = await check_awarded_to_pubkey(badge.id, event.pubkey)
            assert not_yet_awarded, "POAP was already awarded to the pubkey."
            logger.debug(
                f"Creating award for badge {badge.id} and pubkey {event.pubkey}"
            )
            if badge.geohash:
                geohash = gh_encode(json_data["lat"], json_data["long"])
                logger.debug(f"Geohash: {geohash}")
                logger.debug(
                    f"Distance in meters: {geohash_approximate_distance(geohash, badge.geohash)}"
                )
                logger.debug(
                    f"Distance radius in meters: {geohash_haversine_distance(geohash, badge.geohash)}"
                )
                distance = geohash_haversine_distance(geohash, badge.geohash) / 1000
                assert distance < 50, "Seems that you are not in the right place."

            create_award = CreateAward(
                badge_id=badge.id,
                issuer=issuer.id,
                claim_pubkey=event.pubkey,
            )
            award = await create_award_poap(issuer.id, create_award)
            assert award, "Award couldn't be created"

            event = await sign_and_send_to_nostr(issuer, award)
            assert event, "Award couldn't be uploaded to Nostr"

            award.event_id = event.id
            award.event_created_at = event.created_at

            await update_award(award_id=award.id, data=award)
        else:
            logger.debug(f"Message: {clear_text_msg}")
            return

    except Exception as ex:
        logger.error(ex)


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
        logger.debug(f"Creating poap for issuer {issuer.id}, d: {d}, name: {name}")
        poap = POAP(
            id=d[0],
            issuer_id=issuer.id,
            name=name[0] if len(name) else "Imported POAP",
            description=description[0],
            image=image[0],
            thumb=thumb[0] if len(thumb) else None,
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
            id=event.content,
            badge_id=badge[0].split(":")[1],
            issuer=issuer.id,
            claim_pubkey=claim_pubkey[0],
            event_id=event.id,
            event_created_at=event.created_at,
        )
        await create_award_poap(issuer.id, award)

    except Exception as ex:
        logger.error(ex)


# async def _handle_user_profile_event(event: NostrEvent):
#     try:


#     except Exception as ex:
#         logger.error(ex)
