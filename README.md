# System Monitoring with FastAPI and RabbitMQ

Ce projet est composé de deux applications FastAPI qui communiquent via RabbitMQ pour monitorer les informations système en temps réel.

## Architecture

- **Publisher** : Collecte et publie les informations système
- **Consumer** : Reçoit et affiche les informations dans une interface web
- **RabbitMQ** : Broker de messages utilisant un exchange de type fanout

## Configuration

Chaque application possède son propre fichier `.env` pour la configuration :

### Publisher (.env)
```env
RABBITMQ_HOST=192.168.7.6
RABBITMQ_PORT=5672
EXCHANGE_NAME=system_info
APP_PORT=8000
```

### Consumer (.env)
```env
RABBITMQ_HOST=192.168.7.6
RABBITMQ_PORT=5672
EXCHANGE_NAME=system_info
QUEUE_NAME=Consumer
APP_PORT=8003
```

## Prérequis

- Python 3.8+
- RabbitMQ Server
- Les dépendances listées dans `requirements.txt`

## Installation

1. Cloner le repository
2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Démarrage des applications

1. Démarrer le Consumer :
```bash
cd consumer
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

2. Démarrer le Publisher :
```bash
cd publisher
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Utilisation

1. Ouvrir l'interface web : `http://localhost:8003`
2. Pour publier des informations système : `http://localhost:8000/publish`

## Fonctionnement

1. Le Publisher :
   - Endpoint `/publish` qui collecte les informations système
   - Utilise psutil pour obtenir les métriques (CPU, mémoire, disque)
   - Publie les données via RabbitMQ sur l'exchange 'system_info'

2. Le Consumer :
   - Crée une queue nommée 'Consumer' liée à l'exchange
   - Reçoit les messages et les transmet via WebSocket
   - Affiche les données en temps réel dans une interface web

3. RabbitMQ :
   - Exchange de type 'fanout' pour la diffusion des messages
   - Les messages sont persistants (durable=True)
   - La queue est exclusive au consumer

## Interface Web

L'interface web affiche :
- Les métriques système formatées
- Les données brutes JSON
- Le statut de la connexion WebSocket

## Dépannage

1. Si les messages n'apparaissent pas :
   - Vérifier que RabbitMQ est en cours d'exécution
   - Vérifier les logs du consumer
   - Vérifier la console du navigateur pour les erreurs WebSocket

2. Si la connexion échoue :
   - Vérifier les paramètres dans les fichiers .env
   - Vérifier que les ports sont disponibles
   - Vérifier que RabbitMQ accepte les connexions sur l'IP configurée
