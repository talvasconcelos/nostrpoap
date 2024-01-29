import asyncio
from asyncio import Task
from typing import List

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


from .nostr.nostr_client import NostrClient

nostr_client = NostrClient()

scheduled_tasks: List[Task] = []

from .tasks import wait_for_nostr_events
from .views import *
from .views_api import *


def poap_start():
    async def _subscribe_to_nostr_client():
        # wait for 'nostrclient' extension to initialize
        await asyncio.sleep(10)
        await nostr_client.run_forever()

    async def _wait_for_nostr_events():
        # wait for this extension to initialize
        await asyncio.sleep(15)
        await wait_for_nostr_events(nostr_client)

    loop = asyncio.get_event_loop()
    # task1 may be needed in the future
    # task1 = loop.create_task(catch_everything_and_restart(wait_for_paid_invoices))
    task2 = loop.create_task(catch_everything_and_restart(_subscribe_to_nostr_client))
    task3 = loop.create_task(catch_everything_and_restart(_wait_for_nostr_events))
    scheduled_tasks.extend([task2, task3])
