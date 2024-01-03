# Maybe your extensions needs some LNURL stuff, if so checkout LNURLp/LNURLw extensions/lnurl library in LNbits (to keep things simple the below examples are raw LNURLs)


from http import HTTPStatus
from fastapi import Depends, Query, Request
from . import poap_ext
from .crud import get_poap
from lnbits.core.services import create_invoice


#################################################
########### A very simple LNURLpay ##############
# https://github.com/lnurl/luds/blob/luds/06.md #
#################################################
#################################################

@poap_ext.get(
    "/api/v1/lnurl/pay/{poap_id}", 
    status_code=HTTPStatus.OK,
    name="poap.api_lnurl_pay",
)
async def api_lnurl_pay(
    request: Request,
    poap_id: str,
):
    poap = await get_poap(poap_id)
    if not poap:
        return {"status": "ERROR", "reason": "No poap found"}
    return {
            "callback": str(request.url_for("poap.api_lnurl_pay_callback", poap_id=poap_id)),
            "maxSendable": poap.lnurlpayamount,
            "minSendable": poap.lnurlpayamount,
            "metadata":"[[\"text/plain\", \"" + poap.name + "\"]]",
            "tag": "payRequest"
        }

@poap_ext.get(
    "/api/v1/lnurl/pay/cb/{poap_id}", 
    status_code=HTTPStatus.OK,
    name="poap.api_lnurl_pay_callback",
)
async def api_lnurl_pay_cb(
    request: Request,
    poap_id: str,
    amount: int = Query(...),
):
    poap = await get_poap(poap_id)
    if not poap:
        return {"status": "ERROR", "reason": "No poap found"}
    
    payment_request = await create_invoice(
        wallet_id=poap.wallet,
        amount=int(amount / 1000),
        memo=poap.name,
        unhashed_description="[[\"text/plain\", \"" + poap.name + "\"]]".encode(),
        extra= {
            "tag": "poap",
            "link": poap_id,
            "extra": request.query_params.get("amount"),
        },
    )
    return { "pr": payment_request, "routes": []}

#################################################
######## A very simple LNURLwithdraw ############
# https://github.com/lnurl/luds/blob/luds/03.md #
#################################################
#################################################


@poap_ext.get(
    "/api/v1/lnurl/withdraw/{poap_id}",
    status_code=HTTPStatus.OK,
    name="poap.api_lnurl_withdraw",
)
async def api_lnurl_pay(
    request: Request,
    poap_id: str,
):
    poap = await get_poap(poap_id)
    if not poap:
        return {"status": "ERROR", "reason": "No poap found"}
    return {
            "callback": str(request.url_for("poap.api_lnurl_withdraw_callback", poap_id=poap_id)),
            "maxSendable": poap.lnurlwithdrawamount,
            "minSendable": poap.lnurlwithdrawamount,
            "k1": "",
            "defaultDescription": poap.name,
            "metadata":"[[\"text/plain\", \"" + poap.name + "\"]]",
            "tag": "withdrawRequest"
        }

@poap_ext.get(
    "/api/v1/lnurl/pay/cb/{poap_id}", 
    status_code=HTTPStatus.OK,
    name="poap.api_lnurl_withdraw_callback",
)
async def api_lnurl_pay_cb(
    request: Request,
    poap_id: str,
    amount: int = Query(...),
):
    poap = await get_poap(poap_id)
    if not poap:
        return {"status": "ERROR", "reason": "No poap found"}
    
    payment_request = await create_invoice(
        wallet_id=poap.wallet,
        amount=int(amount / 1000),
        memo=poap.name,
        unhashed_description="[[\"text/plain\", \"" + poap.name + "\"]]".encode(),
        extra= {
            "tag": "poap",
            "link": poap_id,
            "extra": request.query_params.get("amount"),
        },
    )
    return { "pr": payment_request, "routes": []}