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
    # update_poap,
    # delete_poap,
    get_poap,
    get_poaps,
)
from .models import CreateIssuer, Issuer, CreatePOAP


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
    issuer = await get_issuer_for_user(wallet.wallet.user)
    if not issuer:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Issuer does not exist."
        )
    poap = await create_poap(issuer_id=issuer.id, data=data)
    return poap.dict()


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


# @poap_ext.post("/api/v1/poaps", status_code=HTTPStatus.CREATED)
# async def api_poap_create(
#     data: CreateTempData, wallet: WalletTypeInfo = Depends(get_key_type)
# ):
#     poap = await create_poap(wallet_id=wallet.wallet.id, data=data)
#     return poap.dict()


## Delete a record


# @poap_ext.delete("/api/v1/poaps/{poap_id}")
# async def api_poap_delete(
#     poap_id: str, wallet: WalletTypeInfo = Depends(require_admin_key)
# ):
#     poap = await get_poap(poap_id)

#     if not poap:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND, detail="Temp does not exist."
#         )

#     if poap.wallet != wallet.wallet.id:
#         raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Not your Temp.")

#     await delete_poap(poap_id)
#     return "", HTTPStatus.NO_CONTENT
