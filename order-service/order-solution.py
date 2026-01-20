import time
import os
from flask import Flask, jsonify
import json
import threading
from confluent_kafka import Consumer, Producer
import re

app = Flask(__name__)

# Port configurable via variable d'environnement (pour lancer plusieurs instances)
PORT = int(os.environ.get('PORT', 8001))

orders = []

# Configuration Kafka
consumer_config = {
        "bootstrap.servers": "localhost:9094",
        "group.id": "order-service-group",
        "auto.offset.reset": "earliest"
}

producer_config = {
        "bootstrap.servers": "localhost:9094"
}

consumer = Consumer(consumer_config)
producer = Producer(producer_config)

def delivery_report(err, msg):
        if err:
                print(f"Échec envoi: {err}")
        else:
                print(f"Message envoyé à {msg.topic()}")

def process_payment_event(message):
        user_id = message.get('user_id')
        cart = message.get('cart')
        
        time.sleep(0.1)
        
        order = {
                'order_id': len(orders) + 1,
                'user_id': user_id,
                'items': cart,
                'status': 'confirmed'
        }
        
        orders.append(order)
        print(f"Nouvelle commande créée: {order}")
        
        # Produire l'événement order-created
        producer.produce(
                topic="order-created",
                value=json.dumps(order).encode("utf-8"),
                callback=delivery_report
        )
        producer.poll(0)

def send_to_dlq(message, error_reason):
    """Envoie un message dans la Dead Letter Queue"""
    dlq_message = {
        "original_message": message.decode('utf-8') if isinstance(message, bytes) else str(message),
        "error": error_reason,
        "timestamp": time.time()
    }

    producer.produce(
        topic="dlq-payment",
        value=json.dumps(dlq_message).encode('utf-8'),
        callback=delivery_report
    )
    producer.poll(0)
    print(f"Message envoyé à la DLQ: {error_reason}")

def kafka_consumer_loop():
    consumer.subscribe(["payment-successful"])
    print("Consumer démarré, en écoute sur 'payment-successful'...")

    while True:
        msg = consumer.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            print(f"Erreur: {msg.error()}")
            continue

        raw_value = msg.value()

        try:
            # 1. Parsing JSON
            data = json.loads(raw_value.decode('utf-8'))

            # 2. Validation des champs requis
            if not isinstance(data.get('user_id'), (int, str)):
                raise ValueError("user_id invalide")
            if not isinstance(data.get('cart'), list):
                raise ValueError("cart doit être une liste")
            if not all(isinstance(item.get('name'), str) for item in data.get('cart', [])):
                raise ValueError("Le nom de chaque item doit être une chaîne de caractères")
            if not all(isinstance(item.get('price'), (int, float)) and item.get('price') > 0 for item in data.get('cart', [])):
                raise ValueError("Le prix de chaque item doit être un nombre positif")
            """if not all(isinstance(item.get('quantity'), int) and item.get('quantity') > 0 for item in data.get('cart', [])):
                raise ValueError("La quantité de chaque item doit être un entier positif")"""
            if any(len(item.get('name', '')) > 100 for item in data.get('cart', [])):
                raise ValueError("Le nom de l'item est trop long")
            if contains_special_chars(str(data.get('user_id'))):
                raise ValueError("Caractères spéciaux détectés dans user_id")
            for item in data.get('cart', []):
                if contains_special_chars(str(item.get('name', ''))):
                    raise ValueError("Caractères spéciaux détectés dans le nom de l'item")
            # 3. Traitement
            process_payment_event(data)

        except json.JSONDecodeError as e:
            print(f"JSON invalide: {e}")
            send_to_dlq(raw_value, str(e))

        except ValueError as e:
            print(f"Validation échouée: {e}")
            send_to_dlq(raw_value, str(e))

        except Exception as e:
            print(f"Erreur inattendue: {e}")
            send_to_dlq(raw_value, str(e))

def contains_special_chars(text):
    # Exemple de détection de caractères potentiellement malveillants
    return bool(re.search(r"[<>'\"%;()&+]", text))


@app.route('/orders', methods=['GET'])
def get_orders():
        return jsonify({"orders": orders}), 200

if __name__ == '__main__':
        # Lancer le consumer dans un thread séparé
        consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
        consumer_thread.start()
        
        print(f"Service de commande démarré sur le port {PORT}")
        app.run(host='0.0.0.0', port=PORT, debug=False)