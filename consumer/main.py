import pika
import json
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio
from threading import Thread
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

app = FastAPI()

# Configuration depuis .env
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
EXCHANGE_NAME = os.getenv('EXCHANGE_NAME', 'system_info')
EXCHANGE_TYPE = os.getenv('EXCHANGE_TYPE', 'fanout')
QUEUE_NAME = os.getenv('QUEUE_NAME', 'Consumer')
QUEUE_EXCLUSIVE = os.getenv('QUEUE_EXCLUSIVE', 'true').lower() == 'true'
WEBSOCKET_HOST = os.getenv('WEBSOCKET_HOST', 'localhost')
WEBSOCKET_PORT = os.getenv('WEBSOCKET_PORT', '8003')

# Stockage des dernières informations reçues
latest_info = {}

def setup_rabbitmq():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT
        )
    )
    channel = connection.channel()
    
    # Déclarer l'exchange
    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type=EXCHANGE_TYPE,
        durable=True
    )
    
    # Créer une queue
    result = channel.queue_declare(
        queue=QUEUE_NAME,
        exclusive=QUEUE_EXCLUSIVE
    )
    queue_name = result.method.queue
    
    # Lier la queue à l'exchange
    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=queue_name
    )
    return connection, channel, queue_name

def callback(ch, method, properties, body):
    global latest_info
    latest_info = json.loads(body)
    print("\n=== Message Reçu ===")
    print(json.dumps(json.loads(body), indent=2))
    print("==================\n")

def start_consuming():
    connection, channel, queue_name = setup_rabbitmq()
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback,
        auto_ack=True
    )
    channel.start_consuming()

# Démarrer le consumer dans un thread séparé
consumer_thread = Thread(target=start_consuming, daemon=True)
consumer_thread.start()

# Page HTML pour afficher les informations
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>System Information Monitor</title>
        <style>
            body { 
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f0f2f5;
            }
            .info-container {
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-top: 20px;
            }
            h1 { color: #1a73e8; }
            .metric {
                margin: 10px 0;
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            .metric-title {
                font-weight: bold;
                color: #5f6368;
            }
            .raw-data {
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 4px;
                font-family: monospace;
                white-space: pre-wrap;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <h1>System Information Monitor</h1>
        <div class="info-container">
            <div id="systemInfo">Waiting for data...</div>
            <div id="rawData" class="raw-data">Waiting for raw data...</div>
        </div>
        <script>
            function connect() {
                var ws = new WebSocket(`ws://${window.location.hostname}:${WEBSOCKET_PORT}/ws`);
                
                ws.onmessage = function(event) {
                    console.log("Message reçu:", event.data);
                    var data = JSON.parse(event.data);
                    
                    var html = `
                        <div class="metric">
                            <span class="metric-title">Timestamp:</span> ${data.timestamp}
                        </div>
                        <div class="metric">
                            <span class="metric-title">CPU Usage:</span> ${data.cpu_percent}%
                        </div>
                        <div class="metric">
                            <span class="metric-title">Memory Usage:</span> ${data.memory.percent}%
                            <br>Total: ${Math.round(data.memory.total / (1024 * 1024 * 1024))} GB
                            <br>Available: ${Math.round(data.memory.available / (1024 * 1024 * 1024))} GB
                        </div>
                        <div class="metric">
                            <span class="metric-title">Disk Usage:</span>
                            <br>Total: ${Math.round(data.disk.total / (1024 * 1024 * 1024))} GB
                            <br>Used: ${Math.round(data.disk.used / (1024 * 1024 * 1024))} GB
                            <br>Free: ${Math.round(data.disk.free / (1024 * 1024 * 1024))} GB
                        </div>
                        <div class="metric">
                            <span class="metric-title">Platform:</span> ${data.platform} ${data.platform_release}
                        </div>
                        <div class="metric">
                            <span class="metric-title">Processor:</span> ${data.processor}
                        </div>
                    `;
                    document.getElementById("systemInfo").innerHTML = html;
                    document.getElementById("rawData").textContent = JSON.stringify(data, null, 2);
                };

                ws.onclose = function() {
                    console.log("WebSocket fermé, tentative de reconnexion dans 2 secondes...");
                    setTimeout(connect, 2000);
                };
            }

            connect();
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("Nouvelle connexion WebSocket établie")
    await websocket.accept()
    try:
        while True:
            if latest_info:
                print("Envoi des données au client WebSocket:", json.dumps(latest_info, indent=2))
                await websocket.send_json(latest_info)
            await asyncio.sleep(1)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()
