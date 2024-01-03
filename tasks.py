import asyncio

from loguru import logger

from lnbits.core.models import Payment
from lnbits.core.services import create_invoice, pay_invoice, websocketUpdater
from lnbits.helpers import get_current_extension_name
from lnbits.tasks import register_invoice_listener

from .crud import get_poap


#######################################
########## RUN YOU TASKS HERE #########
#######################################


# the usual task is to listen to invoices related to this extension

async def wait_for_paid_invoices():
    invoice_queue = asyncio.Queue()
    register_invoice_listener(invoice_queue, get_current_extension_name())

    while True:
        payment = await invoice_queue.get()
        await on_invoice_paid(payment)


# do somethhing when an invoice related top this extension is paid

async def on_invoice_paid(payment: Payment) -> None:
    if payment.extra.get("tag") != "poap":
        return

    poap_id = payment.extra.get("poapId")
    assert poap_id

    poap = await get_poap(poap_id)
    assert poap

    # update something
    
    data_to_update = {
        "total": poap.total + payment.amount
    }

    await update_poap(poap_id=poap_id, **data_to_update.dict())


    # here we could send some data to a websocket on wss://<your-lnbits>/api/v1/ws/<poap_id>

    some_payment_data = {
        "name": poap.name,
        "amount": payment.amount,
        "fee": payment.fee,
        "checking_id": payment.checking_id
    }

    await websocketUpdater(poap_id, str(some_payment_data))
