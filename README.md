# websocket-zero

Zero-boilerplate websocket server/browser client for Python. This project is
currently a proof-of-concept and the API is not stable.

Of particular interest is what browser APIs should look like.


## Pitch

The `wszero` module allows defining a server that responds to websocket
messages. Message encoding is handled by the framework using JSON. Messages
contain an opcode `op` that allows them to be routed to a handler, and carry a
payload of arbitrary key-value pairs.

wszero provides Python server that can exchange messages with many browser
clients, and the browser stubs to send/receive messages from the server.


## Python API

### @on()

`@on(op: str)`

A decorator to create a handler for a particular opcode `op`.

The decorated function or async function should accept a first argument
`client`, indicating the `Client` that sent the message. All other parameters
must be provided by the message, or contain a default argument.

For example, let's imagine a message type `announce`, which has a parameter
`text` containing the announcement text and an optional `channel` parameter:

```python

@on('announce')
def handle_announce(client, text, channel=None):
    ...

```

Or as a coroutine:

```python

@on('announce')
async def handle_announce(client, text, channel=None):
    ...

```

### Special messages

There are two special messages `connect` and `disconnect` that can be
registered to be handled with `@on`. These have no parameters (the client is
the only parameter).

### run_server()

`run_server(port=8000)`

Launch the server, bound to all interfaces, on the port given. This function
does not return until the server exits, so should be called at the end of your
program.


### Client

Each connected client is represented by a `Client` object. Client objects have
a number of public methods:


`Client.send(op: str, **params)`

Send a message to this client only.


`Client.eval_js(script: str)`

Execute some Javascript code in the browser.


### Groups and broadcasting

A single message can be broadcast to many or all connected clients. A system
of groups is used to select clients to send to.

`broadcast(op, [group], **params)`

Broadcast a message, with opcode `op`, to all clients in a group. If no group
is given, then broadcast to all connected clients.


`Client.groups`

The set of groups that this client is in.

`Client.add_to_group(group: str)`

Add the client to a broadcast group named by `group`. This is idempotent, so
will do nothing if the client is already a member of the group.

`Client.remove_from_group(group: str)`

Remove the group from the broadcast group given. This is idempotent, so will
do nothing if the client is not a member of the group.


## Javascript API

`window.HANDLERS`

A mapping of opcode to the function that should be called when a given opcode
is received. The functions are called with a single parameter, which is the
mapping of parameter associated with the message, including the opcode `op`.

`window.send_message(msg)`

Send a websocket message to the server. `msg` must be an Object containing an
attribute `op`.


## Goals

1. Be simple enough for schoolchildren of around 10 or 11 to use. We must
   minimise the typing required, and minimise the amount of knowledge needed to
   use the system.
2. Be a modern Python asyncio framework. But do not require deep asyncio
   knowledge from a user perspective.
3. Do not reinvent client-side technologies. It should be possible to write the
   client side in Javascript using React or Vue, even if wszero offers its own
   shortcuts.
4. Do not become server-driven. The temptation for "easy" Python websocket
   frameworks is to drive all logic from the server. The browser becomes merely
   a UI host. The server sends widgets to the browser and the browser sends all
   its events over the wire. I've seen this pattern implemented a couple of
   times (including by myself for [an MMO]). It works, but with major
   downsides such as latency. Where the server holds significant per-client
   state, this reduces scalability.

[an MMO]: https://github.com/lordmauve/dark-world
