from asyncio import Queue


from .nostr.nostr_client import NostrClient
from .services import process_nostr_message, subscribe_to_all_issuers


async def wait_for_nostr_events(nostr_client: NostrClient):
    await subscribe_to_all_issuers()

    while True:
        message = await nostr_client.get_event()
        print(f"### MSG: {message}")
        await process_nostr_message(message)
