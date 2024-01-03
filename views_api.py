from http import HTTPStatus
import json

import httpx
from fastapi import Depends, Query, Request
from lnurl import decode as decode_lnurl
from loguru import logger
from starlette.exceptions import HTTPException

from lnbits.core.crud import get_user
from lnbits.core.models import Payment
from lnbits.core.services import create_invoice
from lnbits.core.views.api import api_payment
from lnbits.decorators import (
    WalletTypeInfo,
    check_admin,
    get_key_type,
    require_admin_key,
    require_invoice_key,
)

from . import poap_ext
from .crud import (
    create_poap,
    update_poap,
    delete_poap,
    get_poap,
    get_poaps
)
from .models import CreateTempData


#######################################
##### ADD YOUR API ENDPOINTS HERE #####
#######################################

## Get all the records belonging to the user

@poap_ext.get("/api/v1/poaps", status_code=HTTPStatus.OK)
async def api_poaps(
    req: Request, all_wallets: bool = Query(False), wallet: WalletTypeInfo = Depends(get_key_type)
):
    wallet_ids = [wallet.wallet.id]
    if all_wallets:
        user = await get_user(wallet.wallet.user)
        wallet_ids = user.wallet_ids if user else []
    return [poap.dict() for poap in await get_poaps(wallet_ids, req)]


## Get a specific record belonging to a user

@poap_ext.put("/api/v1/poaps/{poap_id}")
async def api_poap_update(
    data: CreateTempData,
    poap_id: str,
    wallet: WalletTypeInfo = Depends(require_admin_key),
):
    if not poap_id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Temp does not exist."
        )
    poap = await get_poap(poap_id)
    assert poap, "Temp couldn't be retrieved"

    if wallet.wallet.id != poap.wallet:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Not your Temp.")
    poap = await update_poap(poap_id=poap_id, **data.dict())
    return poap.dict()


## Create a new record

@poap_ext.post("/api/v1/poaps", status_code=HTTPStatus.CREATED)
async def api_poap_create(
    data: CreateTempData, wallet: WalletTypeInfo = Depends(get_key_type)
):
    poap = await create_poap(wallet_id=wallet.wallet.id, data=data)
    return poap.dict()


## Delete a record

@poap_ext.delete("/api/v1/poaps/{poap_id}")
async def api_poap_delete(
    poap_id: str, wallet: WalletTypeInfo = Depends(require_admin_key)
):
    poap = await get_poap(poap_id)

    if not poap:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Temp does not exist."
        )

    if poap.wallet != wallet.wallet.id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Not your Temp.")

    await delete_poap(poap_id)
    return "", HTTPStatus.NO_CONTENT


# ANY OTHER ENDPOINTS YOU NEED

## This endpoint creates a payment

@poap_ext.post("/api/v1/poaps/payment/{poap_id}", status_code=HTTPStatus.CREATED)
async def api_tpos_create_invoice(
    poap_id: str, amount: int = Query(..., ge=1), memo: str = ""
) -> dict:
    poap = await get_poap(poap_id)

    if not poap:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Temp does not exist."
        )
    
    # we create a payment and add some tags, so tasks.py can grab the payment once its paid

    try:
        payment_hash, payment_request = await create_invoice(
            wallet_id=poap.wallet,
            amount=amount,
            memo=f"{memo} to {poap.name}" if memo else f"{poap.name}",
            extra={
                "tag": "poap",
                "tipAmount": tipAmount,
                "poapId": poapId,
                "amount": amount,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

    return {"payment_hash": payment_hash, "payment_request": payment_request}