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
    create_award_poap,
    update_award,
    check_awarded_to_pubkey,
    get_awards,
    delete_issuer_poaps,
    delete_issuer_awards,
    delete_issuer,
)
from .models import CreateIssuer, Issuer, CreatePOAP, CreateAward
from .services import (
    sign_and_send_to_nostr,
    resubscribe_to_all_issuers,
    update_issuer_to_nostr,
    subscribe_to_all_issuers,
)
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


@poap_ext.delete("/api/v1/issuer/{issuer_id}")
async def api_delete_issuer(
    issuer_id: str,
    wallet: WalletTypeInfo = Depends(require_admin_key),
):
    try:
        issuer = await get_issuer_for_user(wallet.wallet.user)
        assert issuer, "Issuer not found"
        assert issuer.id == issuer_id, "You are not the owner of this issuer"

        await delete_issuer_poaps(issuer.id)
        await delete_issuer_awards(issuer.id)

        await delete_issuer(issuer.id)

    except AssertionError as ex:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(ex),
        )
    except Exception as ex:
        logger.warning(ex)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Cannot get merchant",
        )
    finally:
        await subscribe_to_all_issuers()


@poap_ext.put("/api/v1/issuer/{issuer_id}/nostr")
async def api_republish_issuer(
    issuer_id: str, wallet: WalletTypeInfo = Depends(require_admin_key)
):
    try:
        issuer = await get_issuer_for_user(wallet.wallet.user)
        assert issuer, "Issuer not found"
        assert issuer.id == issuer_id, "You are not the owner of this issuer"

    except AssertionError as ex:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(ex),
        )
    except Exception as ex:
        logger.warning(ex)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Cannot republish to Nostr",
        )


@poap_ext.get("/api/v1/issuer/{issuer_id}/nostr")
async def api_refresh_issuer(
    issuer_id: str,
    wallet: WalletTypeInfo = Depends(require_admin_key),
):
    try:
        issuer = await get_issuer_for_user(wallet.wallet.user)
        assert issuer, "Issuer not found"
        assert issuer.id == issuer_id, "You are not the owner of this issuer"

        issuer = await update_issuer_to_nostr(issuer)

        await nostr_client.issuer_temp_subscription(issuer.public_key)

    except AssertionError as ex:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(ex),
        )
    except Exception as ex:
        logger.warning(ex)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Cannot refresh from nostr",
        )


# @poap_ext.delete("/api/v1/issuer/{issuer_id}/nostr")
# async def api_delete_issuer(
#     issuer_id: str,
#     wallet: WalletTypeInfo = Depends(require_admin_key),
# ):
#     try:
#         issuer = await get_issuer_for_user(wallet.wallet.user)
#         assert issuer, "Issuer not found"
#         assert issuer.id == issuer_id, "You are not the owner of this issuer"

#         merchant = await update_issuer_to_nostr(issuer, True)
#         await update_issuer(wallet.wallet.user, merchant.id, merchant.config)

#     except AssertionError as ex:
#         raise HTTPException(
#             status_code=HTTPStatus.BAD_REQUEST,
#             detail=str(ex),
#         )
#     except Exception as ex:
#         logger.warning(ex)
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail="Cannot get merchant",
#         )

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

        await update_poap(issuer_id=issuer.id, data=poap)
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


## upate a badge
@poap_ext.put("/api/v1/poaps/{poap_id}", status_code=HTTPStatus.OK)
async def api_poap_update(
    poap_id: str,
    data: CreatePOAP,
    wallet: WalletTypeInfo = Depends(require_admin_key),
):
    try:
        issuer = await get_issuer_for_user(wallet.wallet.user)
        assert issuer, "Issuer not found"

        poap = await update_poap(issuer_id=issuer.id, data=data)
        assert poap, "POAP couldn't be retrieved"

        event = await sign_and_send_to_nostr(issuer, poap)

        poap.event_id = event.id
        await update_poap(issuer_id=issuer.id, data=poap)
        return poap

    except (ValueError, AssertionError) as ex:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(ex),
        )
    except Exception as ex:
        logger.warning(ex)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Cannot update badge",
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
async def api_get_poap(
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
@poap_ext.post("/api/v1/award", status_code=HTTPStatus.CREATED)
async def api_poap_award(
    data: CreateAward,
    request: Request,
):
    if not data.badge_id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="POAP does not exist."
        )
    if not data.claim_pubkey:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Public key not found."
        )
    try:
        not_yet_awarded = await check_awarded_to_pubkey(
            data.badge_id, data.claim_pubkey
        )
        assert not_yet_awarded, "POAP was already awarded to your pubkey."

        poap = await get_poap(data.badge_id)
        assert poap, "POAP couldn't be retrieved"

        issuer = await get_issuer(data.issuer)
        if not issuer:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Issuer does not exist."
            )

        award = await create_award_poap(issuer.id, data)
        assert award, "Award couldn't be created"

        event = await sign_and_send_to_nostr(issuer, award)
        assert event, "Award couldn't be uploaded to Nostr"

        award.event_id = event.id
        award.event_created_at = event.created_at

        await update_award(award_id=award.id, data=award)
        return

    except (ValueError, AssertionError) as ex:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(ex),
        )
    except Exception as ex:
        logger.warning(ex)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Cannot award badge",
        )


@poap_ext.get("/api/v1/awards", status_code=HTTPStatus.OK)
async def api_awards(
    wallet: WalletTypeInfo = Depends(require_invoice_key),
):
    issuer = await get_issuer_for_user(wallet.wallet.user)
    if not issuer:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Issuer does not exist."
        )
    return [award.dict() for award in await get_awards(issuer.id)]
