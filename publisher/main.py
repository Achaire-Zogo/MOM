import psutil
import json
import pika
from fastapi import FastAPI
from datetime import datetime
import platform
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

app = FastAPI()

# Configuration RabbitMQ depuis .env
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
EXCHANGE_NAME = os.getenv('EXCHANGE_NAME', 'system_info')
EXCHANGE_TYPE = os.getenv('EXCHANGE_TYPE', 'fanout')

def setup_rabbitmq():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT
        )
    )
    channel = connection.channel()
    # Déclarer l'exchange de type fanout
    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type=EXCHANGE_TYPE,
        durable=True
    )
    return connection, channel

def get_system_info():
    info = {
        'timestamp': datetime.now().isoformat(),
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory': {
            'total': psutil.virtual_memory().total,
            'available': psutil.virtual_memory().available,
            'percent': psutil.virtual_memory().percent
        },
        'disk': {
            'total': psutil.disk_usage('/').total,
            'used': psutil.disk_usage('/').used,
            'free': psutil.disk_usage('/').free
        },
        'platform': platform.system(),
        'platform_release': platform.release(),
        'processor': platform.processor()
    }
    return info

@app.get("/publish")
async def publish_system_info():
    try:
        connection, channel = setup_rabbitmq()
        system_info = get_system_info()
        
        # Publier le message
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key='',  # Non utilisé pour fanout
            body=json.dumps(system_info)
        )
        
        connection.close()
        return {"status": "success", "message": "System information published", "data": system_info}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    return {"message": "System Info Publisher Service"}
