import asyncio

from fastapi import APIRouter

from lnbits.db import Database
from lnbits.helpers import template_renderer
from lnbits.tasks import catch_everything_and_restart

db = Database("ext_poap")

poap_ext: APIRouter = APIRouter(prefix="/poap", tags=["POAP"])

poap_static_files = [
    {
        "path": "/poap/static",
        "name": "poap_static",
    }
]


def poap_renderer():
    return template_renderer(["poap/templates"])


# from .tasks import wait_for_paid_invoices
from .views import *
from .views_api import *


# def poap_start():
#     loop = asyncio.get_event_loop()
#     loop.create_task(catch_everything_and_restart(wait_for_paid_invoices))
