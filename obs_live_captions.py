#!/usr/bin/env python3

import asyncio
import json
import os
import subprocess
import sys
import time
import websockets

from datetime import datetime
from flask import Flask, request, Response
from pathlib import Path

######################################################################
# Config 
######################################################################

domain = 'localhost'
http_port = '5050'
ws_port = '5051'
transcript_dir = os.path.join(Path.home(), 'obs-live-transcripts')

font_color = "#bbbbbb"
font_family = 'Constantia, "Lucida Bright", Lucidabright, "Lucida Serif", Lucida, "DejaVu Serif", "Bitstream Vera Serif", "Liberation Serif", Georgia, serif'
container_height = "7.2rem"
container_width = "10rem"

#######################################################################

### Pathing 

python_path = sys.executable
script_path = os.path.realpath(__file__) 

### Setup transcript
Path(transcript_dir).mkdir(parents=True, exist_ok=True)
transcript_file_name = f'obs-live-transcript-{datetime.now().strftime("%Y-%m-%d--%H-%M-%S")}.txt'
transcript_file_path = f'{transcript_dir}/{transcript_file_name}'

def write_to_transcript(text):
    with open(transcript_file_path, 'a') as _file:
        _file.write(f"{datetime.now().strftime('%Y-%m-%d--%H-%M-%S')} ~ ")
        _file.write(f"{text.strip()}\n\n")


### Flask Stuff
app = Flask(__name__)

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
            background: #eee;
            font-family: Sans-Serif;
        }
        .container {
            height: 3.4rem;
            width: 20rem;
            position: relative;
            overflow: hidden;
            border: 1px solid black;
            padding: 2px;
        }
        .content {
            color: #000;
            position: absolute;
            bottom: 0;
        }
    </style>
</head>
<body>
    <h3>OBS Live Captions</h3>
    <p>To use the live captions:
    <ol>
    <li>Click 'Allow' when the browser asks to use your microphone'</li>
    <li>Create a new Browser Source in OBS with <a href="/obs">this link</a> and crop in to the outlined box on it.</li>
    </ol>
    <p>You can also configure the display formatting in the config section towards the top of the .py file</p>


    <div class="container">
        <div class="content" id="transcript"></div>
    </div>
    <hr>
    <p><a href="/obs" target="_blank">Open page for OBS Browser Source</a></p>

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


        try {

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
                        ws.send(`{"text": "${new_text}", "isFinal": true }`)
                    }
                }

                else if (new_text.length > long_text.length) {
                    long_text = new_text
                    ts.innerHTML = new_text
                    if (safe_to_send) {
                        ws.send(`{"text": "${new_text}", "isFinal": false }`)
                    }
                }
            }
        } catch (error) {
            ts.innerHTML = "This browser doesn't support the necessary WebSpeech API. Try using Google Chrome"; 
        }


    </script>
</body>
</html>
"""

    return Response(
        status=200,
        response=main_html
    )


@app.route('/obs', methods=['GET'])
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
    """
    obs_html += f"font-family: {font_family};\n"
    obs_html += f"height: {container_height};\n"
    obs_html += f"width: {container_width};\n"
    obs_html += """ 
            position: relative;
            overflow: hidden;
            padding: 1rem;
            border: 1px solid gray;
        }
        .content {
"""
    obs_html += f"color: {font_color};\n"

    obs_html += """
        position: absolute;
            bottom: 0;
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
    



### Websocket stuff 

CONNECTIONS =  set()

async def register(websocket):
    CONNECTIONS.add(websocket)

async def unregister(websocket):
    CONNECTIONS.remove(websocket)

async def notify_users(message, websocket):
    connection_list = []
    for connection in CONNECTIONS:
        connection_list.append(connection)

    await asyncio.wait([
        connection.send(message) for connection in connection_list
    ])


async def message_control(websocket, path):
    await register(websocket)
    try:
        await websocket.send("Connected")
        async for message in websocket:
            print(message)
            message_data = json.loads(message)  
            if message_data['isFinal']:
                write_to_transcript(message_data['text'])

            await notify_users(message_data['text'], websocket)
    finally:
        await unregister(websocket)



if len(sys.argv) == 2: 
    if sys.argv[1] == 'run_websockets':
        print("\nStarting websocket server")
        start_server = websockets.serve(message_control, domain, ws_port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

else:
    time.sleep(1)
    print("Triggering websocket server")
    return_value = (subprocess.Popen([
        python_path,
        script_path,
        'run_websockets'
    ]))

    print("Starting flask web server")
    app.run(port=http_port)

