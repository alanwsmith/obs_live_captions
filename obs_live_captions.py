#!/usr/bin/env python3

from flask import Flask, request, Response
from flask_socketio import SocketIO

async_mode=None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# socketio.init_app(app, cors_allowed_origins='*')
socketio = SocketIO(app, async_mode=async_mode)

domain = '127.0.0.1'
ws_port = '5000'

@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)


@app.route('/', methods=['GET'])
def home_page():
    main_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OBS Live Captions</title>
    <style>
        body {
            background: #000;
            font-family: Sans-Serif;
        }
        .container {
            height: 3.3rem;
            width: 20rem;
            position: relative;
            overflow: hidden;
            border: 1px solid black;
            background: black;
        }
        .content {
            color: #fff;
            position: absolute;
            bottom: 0;
        }
        td {
            font-size: 0.65rem;
        }
        #debug_stuff {
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="content" id="transcript"></div>
    </div>
    <hr>

    <script>

        let safe_to_send = false
"""

    main_html += f'let ws = new WebSocket("ws://{domain}:{ws_port}/");'

    main_html += """
ws.addEventListener('open', (event) => {
            safe_to_send = true
        })

        let restart = true

        let ts = document.getElementById('transcript')

        var SpeechRecognition = SpeechRecognition || webkitSpeechRecognition;
        var recognition = new SpeechRecognition();

        recognition.continuous = true;
        recognition.lang = 'en-US';
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;

        document.addEventListener("DOMContentLoaded", recognition.start());

        // Restart if the service stops
        recognition.addEventListener("end", function () {
            console.log("restarting process");
            recognition.start();
        })

        let results_counter = 0
        let long_text = ""
        // let count_of_results = 0

        let active_index = 0

        recognition.onresult = function(event) {

            results_counter += 1;
            let isFinal = true
            let new_text = "";

            for (let i = 0; i < event.results.length; i = i + 1) {
                if (event.results[i].isFinal == false) {
                    if (i > active_index){
                        long_text = ""
                        active_index = i
                    }
                    isFinal = false
                    new_text = event.results[i][0].transcript;
                    break;
                }
            }

            if (isFinal === true) {
                last_result_index = event.results.length - 1;
                new_text = event.results[last_result_index][0].transcript;
                long_text = ""
                ts.innerHTML = new_text
                if (safe_to_send) {
                    ws.send(new_text)
                }
            }

            else if (new_text.length > long_text.length) {
                long_text = new_text
                ts.innerHTML = new_text
                if (safe_to_send) {
                    ws.send(new_text)
                }
            }
        }

    </script>
</body>
</html>
"""

    return Response(
        status=200,
        response=main_html
    )


@app.route('/obs.html', methods=['GET'])
def obs_page():
    obs_html = """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Captions For OBS</title>
        <style>
        body {
            background:  rgba(180, 180, 0, 0);
            font-family: Sans-Serif;
        }
        .container {
            height: 2.2rem;
            width: 20rem;
            position: relative;
            overflow: hidden;
        }
        .content {
            color: #aaa;
            position: absolute;
            bottom: 0;
        }
        td {
            font-size: 1rem;
        }
        #debug_stuff {
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="content" id="transcript"></div>
    </div>
    <script>
"""
    obs_html += f'const ws = new WebSocket("ws://{domain}:{ws_port}/")'
    
    obs_html += """
        ws.onmessage = function (event) {
            document.getElementById('transcript').innerHTML = event.data
        }
    </script>
</body>
</html>
"""

    return Response(
        status=200,
        response=obs_html
    )
    
if __name__ == "__main__":
    socketio.run(app, debug=True)



