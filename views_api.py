from http import HTTPStatus
from typing import Optional

from fastapi import Depends, Request
from loguru import logger
from starlette.exceptions import HTTPException

from lnbits.decorators import (
    WalletTypeInfo,
    require_admin_key,
    require_invoice_key,
)

from . import poap_ext
from .crud import (
    get_issuer,
    create_issuer,
    get_issuer_by_pubkey,
    get_issuer_for_user,
    create_poap,
    update_poap,
    # delete_poap,
    get_poap,
    get_poaps,
)
from .models import CreateIssuer, Issuer, CreatePOAP
from .services import sign_and_send_to_nostr, resubscribe_to_all_issuers
from . import nostr_client


@poap_ext.post("/api/v1/issuer")
async def api_create_issuer(
    data: CreateIssuer,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> Issuer:
    try:
        issuer = await get_issuer_by_pubkey(data.public_key)
        if issuer:
            raise AssertionError("An issuer already exists with this public key")

        issuer = await get_issuer_for_user(wallet.wallet.user)
        if issuer:
            raise AssertionError("An issuer already exists for this user")

        issuer = await create_issuer(wallet.wallet.user, data)

        await resubscribe_to_all_issuers()

        await nostr_client.issuer_temp_subscription(issuer.public_key)

        return issuer
    except AssertionError as ex:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(ex),
        )
    except Exception as ex:
        logger.warning(ex)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Cannot create issuer",
        )


@poap_ext.get("/api/v1/issuer")
async def api_get_issuer(
    wallet: WalletTypeInfo = Depends(require_invoice_key),
) -> Optional[Issuer]:
    try:
        issuer = await get_issuer_for_user(wallet.wallet.user)
        if not issuer:
            return

        return issuer
    except Exception as ex:
        logger.warning(ex)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Cannot get issuer",
        )


## Create a new badge


@poap_ext.post("/api/v1/poaps", status_code=HTTPStatus.CREATED)
async def api_poap_create(
    data: CreatePOAP, wallet: WalletTypeInfo = Depends(require_admin_key)
):
    try:
        issuer = await get_issuer_for_user(wallet.wallet.user)
        if not issuer:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Issuer does not exist."
            )

        poap = await create_poap(issuer_id=issuer.id, data=data)
        assert poap, "POAP couldn't be created"

        event = await sign_and_send_to_nostr(issuer, poap)
        assert event, "POAP couldn't be uploaded to Nostr"
        logger.debug(f"POAP uploaded to Nostr: {event}")

        poap.event_id = event.id
        poap.event_created_at = event.created_at

        await update_poap(badge_id=poap.id, data=poap)
        return poap.dict()

    except (ValueError, AssertionError) as ex:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(ex),
        )
    except Exception as ex:
        logger.warning(ex)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Cannot create badge",
        )


## Get all poaps belonging to the user


@poap_ext.get("/api/v1/poaps", status_code=HTTPStatus.OK)
async def api_poaps(
    wallet: WalletTypeInfo = Depends(require_invoice_key),
):
    issuer = await get_issuer_for_user(wallet.wallet.user)
    if not issuer:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Issuer does not exist."
        )
    return [poap.dict() for poap in await get_poaps(issuer.id)]


## Get a specific poap belonging to a user


@poap_ext.get("/api/v1/poaps/{poap_id}")
async def api_poap_update(
    poap_id: str,
    wallet: WalletTypeInfo = Depends(require_invoice_key),
):
    if not poap_id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="POAP does not exist."
        )
    poap = await get_poap(poap_id)
    assert poap, "POAP couldn't be retrieved"

    return poap.dict()


## Award a POAP
@poap_ext.post("/api/v1/award/{poap_id}/{pubkey}", status_code=HTTPStatus.CREATED)
async def api_poap_award(
    poap_id: str,
    pubkey: str,
    request: Request,
):
    if not poap_id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="POAP does not exist."
        )
    if not pubkey:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Public key not found."
        )
    poap = await get_poap(poap_id)
    assert poap, "POAP couldn't be retrieved"

    issuer = await get_issuer(poap.issuer_id)
    if not issuer:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Issuer does not exist."
        )

    data = await request.json()
    if not data.get("claim_pubkey"):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Missing claim_pubkey"
        )
