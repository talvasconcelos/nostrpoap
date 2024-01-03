from typing import List, Optional, Union

from lnbits.helpers import urlsafe_short_hash

from . import db
from .models import CreateTempData, Temp
from loguru import logger
from fastapi import Request
from lnurl import encode as lnurl_encode

async def create_poap(wallet_id: str, data: CreateTempData) -> Temp:
    poap_id = urlsafe_short_hash()
    await db.execute(
        """
        INSERT INTO poapextension.poap (id, wallet, name, lnurlpayamount, lnurlwithdrawamount)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            poap_id,
            wallet_id,
            data.name,
            data.lnurlpayamount,
            data.lnurlwithdrawamount
        ),
    )
    poap = await get_poap(poap_id)
    assert poap, "Newly created poap couldn't be retrieved"
    return poap


async def get_poap(poap_id: str) -> Optional[Temp]:
    row = await db.fetchone("SELECT * FROM poapextension.poap WHERE id = ?", (poap_id,))
    return Temp(**row) if row else None

async def get_poaps(wallet_ids: Union[str, List[str]], req: Request) -> List[Temp]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]

    q = ",".join(["?"] * len(wallet_ids))
    rows = await db.fetchall(
        f"SELECT * FROM poapextension.poap WHERE wallet IN ({q})", (*wallet_ids,)
    )
    poapRows = [Temp(**row) for row in rows]
    logger.debug(req.url_for("poap.api_lnurl_pay", poap_id=row.id))
    for row in poapRows:
        row.lnurlpay = req.url_for("poap.api_lnurl_pay", poap_id=row.id)
        row.lnurlwithdraw = req.url_for("poap.api_lnurl_withdraw", poap_id=row.id)
    return poapRows

async def update_poap(poap_id: str, **kwargs) -> Temp:
    q = ", ".join([f"{field[0]} = ?" for field in kwargs.items()])
    await db.execute(
        f"UPDATE poapextension.poap SET {q} WHERE id = ?", (*kwargs.values(), poap_id)
    )
    poap = await get_poap(poap_id)
    assert poap, "Newly updated poap couldn't be retrieved"
    return poap

async def delete_poap(poap_id: str) -> None:
    await db.execute("DELETE FROM poapextension.poap WHERE id = ?", (poap_id,))