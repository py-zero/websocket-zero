import asyncio
import weakref
from collections import defaultdict
import inspect
import traceback
import json
import sys

import aiohttp
from aiohttp import web


HANDLERS = {}


class Client:
    # Groups of clients
    groups = defaultdict(weakref.WeakSet)
    connected = groups['__all__']

    def __init__(self, name: str, ws: web.WebSocketResponse):
        self.name = name
        self.outqueue = asyncio.Queue()
        self.ws = ws
        self.groups = set()
        Client.connected.add(self)

    def __repr__(self):
        return f'<Client: {self.name!r}>'

    def add_to_group(self, name: str):
        """Add this client to a group."""
        if name.startswith('_'):
            raise ValueError("Groups beginning with _ are used by wszero")
        self.groups.add(name)
        Client.groups[name].add(self)

    def remove_from_group(self, name: str):
        """Remove this client from a group."""
        if name.startswith('_'):
            raise ValueError("Groups beginning with _ are used by wszero")
        self.groups.discard(name)
        Client.groups[name].discard(self)

    def send(self, op, **params):
        self.outqueue.put_nowait(json.dumps({
            **params,
            'op': op,
        }))

    def eval_js(self, script):
        self.send('eval_js', script=script)

    def write(self, msg):
        """Write a message to the client."""
        self._write(json.dumps(msg))

    def _write(self, msg):
        self.outqueue.put_nowait(msg)

    def handle_auth(self, name, token):
        if self.name:
            return self.write({
                'op': 'authfail',
                'reason': 'You are already authenticated'
            })

        if not re.match(r'^[a-z][a-z_0-9]*[a-z]$', name, flags=re.I):
            return self.write({
                'op': 'authfail',
                'reason': 'Invalid name; please use only lowercase letters ' +
                          'and numbers'
            })
        data = self.load_user_data(name) or {}
        if data:
            if token != data['token']:
                return self.write({
                    'op': 'authfail',
                    'reason': 'Invalid authentication token',
                })

        if name in self.clients:
            return self.write({
                'op': 'authfail',
                'reason': 'You are already connected',
            })

        self.token = token
        self.clients[name] = self
        print(f"{name} connected")
        Client.broadcast({
            'op': 'announce',
            'msg': f"{name} connected"
        })
        self.write({'op': 'authok'})

    async def sender(self):
        while True:
            msg = await self.outqueue.get()
            if not msg:
                break
            await self.ws.send_str(msg)

    async def receiver(self):
        await self._dispatch('connect')
        try:
            async for m in self.ws:
                await asyncio.sleep(0.1)  # TODO: better rate-limiting
                msg = m.json()
                op = msg.pop('op')
                await self._dispatch(op, msg)
        finally:
            await self._dispatch('disconnect')
            self.outqueue.put_nowait(None)

    async def _dispatch(self, op, params={}):
        try:
            handler = HANDLERS[op]
        except KeyError:
            print(f"No handler for operation {op}", file=sys.stderr)
            return

        try:
            if inspect.iscoroutinefunction(handler):
                await handler(self, **params)
            else:
                handler(self, **params)
        except Exception as e:
            traceback.print_exc()
            self.write({
                'op': 'error',
                'msg': f'{type(e).__name__}: {e}',
            })


def broadcast(op, group='__all__', **params):
    """Broadcast a message to all clients in a group."""
    clients = list(Client.groups[group])
    data = json.dumps({
        'op': op,
        **params,
    })
    for c in clients:
        c.outqueue.put_nowait(data)


async def index(request):
    """Serve the index page."""
    with open('assets/index.html') as f:
        return web.Response(
            content_type='text/html',
            text=f.read()
        )


async def open_ws(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    c = Client(request.remote, ws)
    loop.create_task(c.sender())
    await c.receiver()
    return web.Response()


def on(event_name: str):
    """Decorator to bind a handler for a type of event."""
    def dec(func):
        HANDLERS[event_name] = func
        return func
    return dec


app = web.Application()
app.add_routes([
    web.get('/', index),
    web.get('/ws', open_ws),
    web.static('/', 'assets'),
])


async def on_shutdown(app):
    connected = list(Client.connected)
    for c in connected:
        ws = c.ws
        await ws.close(
            code=aiohttp.WSCloseCode.GOING_AWAY,
            message='Server shutdown'
        )


app.on_shutdown.append(on_shutdown)
loop = asyncio.get_event_loop()


def run_server(*, port=8000):
    """Run the server."""
    web.run_app(app, port=port)


if __name__ == '__main__':
    run_server()
