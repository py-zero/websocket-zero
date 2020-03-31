from wszero import on, run_server


@on('connect')
def handle_connect(client):
    print("Client connected:", client)
    client.eval_js("""
    document.title = 'Where is Kazakhstan';
    """)


@on('disconnect')
def handle_disconnect(client):
    print("Client disconnected:", client)


run_server()
