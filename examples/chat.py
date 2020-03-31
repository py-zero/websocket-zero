from wszero import on, run_server, broadcast


@on('connect')
def handle_connect(client):
    print("Client connected:", client)
    client.eval_js("""
    document.title = 'Chat demo';
    var name = prompt('What is your name?');
    send_msg({op: 'name', name: name});
    """)


@on('name')
def handle_name(client, name):
    print(f"Client {client.name} renamed to {name}")
    client.name = name
    broadcast('chatmsg', sender=client.name, text='connected')

    client.eval_js("""
    document.body.innerHTML = '';
    inp = document.createElement('input');
    document.body.appendChild(inp);
    inp.addEventListener(
        'keydown',
        (event) => {
            if (event.keyCode == 13) {
                send_msg({op: 'chatmsg', text: inp.value});
                inp.value = '';
            }
        },
        false
    );

    log = document.createElement('div');
    document.body.appendChild(log);

    HANDLERS['chatmsg'] = (params) => {
        const div = document.createElement('div');
        const name = document.createElement('strong');
        name.innerText = params.sender;
        const text = document.createTextNode(' ' + params.text);
        div.appendChild(name);
        div.appendChild(text);
        log.appendChild(div);
    };
    """)


@on('chatmsg')
def handle_msg(client, text):
    broadcast('chatmsg', sender=client.name, text=text)
    print(f"{client.name}: {text}")


@on('disconnect')
def handle_disconnect(client):
    print("Client disconnected:", client)
    broadcast('chatmsg', sender=client.name, text='disconnected')


run_server()
