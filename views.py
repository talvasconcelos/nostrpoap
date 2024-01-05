from http import HTTPStatus

from fastapi import Depends, Request
from fastapi.poaplating import Jinja2Templates
from starlette.exceptions import HTTPException
from starlette.responses import HTMLResponse

from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.settings import settings

from . import poap_ext, poap_renderer
from .crud import get_poap

poaps = Jinja2Templates(directory="poaps")


# Backend admin page


@poap_ext.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_user_exists)):
    return poap_renderer().TemplateResponse(
        "poap/index.html", {"request": request, "user": user.dict()}
    )


# Frontend shareable page


@poap_ext.get("/{poap_id}")
async def poap(request: Request, poap_id):
    poap = await get_poap(poap_id)
    if not poap:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Temp does not exist."
        )
    return poap_renderer().TemplateResponse(
        "poap/poap.html",
        {
            "request": request,
            "poap_id": poap_id,
            "lnurlpay": poap.lnurlpayamount,
            "lnurlwithdraw": poap.lnurlwithdrawamount,
            "web_manifest": f"/poap/manifest/{poap_id}.webmanifest",
        },
    )


# Manifest for public page, customise or remove manifest completely

# @poap_ext.get("/manifest/{poap_id}.webmanifest")
# async def manifest(poap_id: str):
#     poap= await get_poap(poap_id)
#     if not poap:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND, detail="Temp does not exist."
#         )

#     return {
#         "short_name": settings.lnbits_site_title,
#         "name": poap.name + " - " + settings.lnbits_site_title,
#         "icons": [
#             {
#                 "src": settings.lnbits_custom_logo
#                 if settings.lnbits_custom_logo
#                 else "https://cdn.jsdelivr.net/gh/lnbits/lnbits@0.3.0/docs/logos/lnbits.png",
#                 "type": "image/png",
#                 "sizes": "900x900",
#             }
#         ],
#         "start_url": "/poap/" + poap_id,
#         "background_color": "#1F2234",
#         "description": "Minimal extension to build on",
#         "display": "standalone",
#         "scope": "/poap/" + poap_id,
#         "theme_color": "#1F2234",
#         "shortcuts": [
#             {
#                 "name": poap.name + " - " + settings.lnbits_site_title,
#                 "short_name": poap.name,
#                 "description": poap.name + " - " + settings.lnbits_site_title,
#                 "url": "/poap/" + poap_id,
#             }
#         ],
#     }
