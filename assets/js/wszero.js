function send_msg(msg) {
    ws.send(JSON.stringify(msg));
}

HANDLERS = {
    'eval_js': function (params) {
        eval(params.script);
    },
    'error': function (params) {
        console.error(params.msg);
    },
};

function connect() {
    ws = new WebSocket("ws://" + location.host + "/ws");

    ws.onopen = function () {
        console.log('Connection established');
    };
    ws.onmessage = function (event) {
        let params = JSON.parse(event.data);
        let h = HANDLERS[params.op];
        if (!h) {
            throw "no handler for " + params.op;
        }
        h(params);
    };
    ws.onclose = function (event) {
        console.log('Connection closed: ' + event.code + ' ' + event.reason, 'error');
        setTimeout(connect, 2000);
    };
}

window.addEventListener('load', connect, false);
