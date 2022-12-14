import time
import json
import asyncio

from .. import Client, BfxWebsocket


def get_now():
    return int(round(time.time() * 1000))


class StubbedWebsocket(BfxWebsocket):
    def __new__(cls, *args, **kwargs):
        instance = super(StubbedWebsocket, cls).__new__(cls, *args, **kwargs)
        instance.sent_items = []
        instance.published_items = []
        return instance

    async def _main(self, host):
        print("Faking wesocket connection to {}".format(host))

    async def publish(self, data, is_json=True):
        self.published_items += [{"time": get_now(), "data": data}]
        # convert to string and push through the websocket
        data = json.dumps(data) if is_json else data
        return await self.on_message(data)

    async def publish_auth_confirmation(self):
        return self.publish(
            {
                "event": "auth",
                "status": "OK",
                "chanId": 0,
                "userId": 269499,
                "auth_id": "58aa0472-b1a9-4690-8ab8-300d68e66aaf",
                "caps": {
                    "orders": {"read": 1, "write": 1},
                    "account": {"read": 1, "write": 0},
                    "funding": {"read": 1, "write": 1},
                    "history": {"read": 1, "write": 0},
                    "wallets": {"read": 1, "write": 1},
                    "withdraw": {"read": 0, "write": 1},
                    "positions": {"read": 1, "write": 1},
                },
            }
        )

    async def send(self, data_string):
        self.sent_items += [{"time": get_now(), "data": data_string}]

    def get_published_items(self):
        return self.published_items

    def get_sent_items(self):
        return self.sent_items

    def get_last_sent_item(self):
        return self.sent_items[-1:][0]

    def get_sent_items_count(self):
        return len(self.sent_items)


class EventWatcher:
    def __init__(self, ws, event):
        self.value = None
        self.event = event
        ws.once(event, self._finish)

    def _finish(self, value):
        self.value = value or {}

    @classmethod
    def watch(cls, ws, event):
        return EventWatcher(ws, event)

    def wait_until_complete(self, max_wait_time=5):
        counter = 0
        while self.value == None:
            if counter > 5:
                raise Exception(
                    "Wait time limit exceeded for event {}".format(self.event)
                )
            time.sleep(1)
            counter += 1
        return self.value


def create_stubbed_client(*args, **kwargs):
    client = Client(*args, **kwargs)
    # no support for rest stubbing yet
    client.rest = None
    client.ws = StubbedWebsocket(*args, **kwargs)
    return client


async def ws_publish_auth_accepted(ws):
    return await ws.publish(
        {
            "event": "auth",
            "status": "OK",
            "chanId": 0,
            "userId": 269499,
            "auth_id": "58aa0472-b1a9-4690-8ab8-300d68e66aaf",
            "caps": {
                "orders": {"read": 1, "write": 1},
                "account": {"read": 1, "write": 0},
                "funding": {"read": 1, "write": 1},
                "history": {"read": 1, "write": 0},
                "wallets": {"read": 1, "write": 1},
                "withdraw": {"read": 0, "write": 1},
                "positions": {"read": 1, "write": 1},
            },
        }
    )


async def ws_publish_connection_init(ws):
    return await ws.publish(
        {
            "event": "info",
            "version": 2,
            "serverId": "748c00f2-250b-46bb-8519-ce1d7d68e4f0",
            "platform": {"status": 1},
        }
    )


async def ws_publish_conf_accepted(ws, flags_code):
    return await ws.publish({"event": "conf", "status": "OK", "flags": flags_code})
