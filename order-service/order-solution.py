import time
import os
from flask import Flask, jsonify
import json
import threading
from confluent_kafka import Consumer, Producer

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
                        
                try:
                        data = json.loads(msg.value().decode('utf-8'))
                        process_payment_event(data)
                except Exception as e:
                        print(f"Erreur de traitement: {e}")

@app.route('/orders', methods=['GET'])
def get_orders():
        return jsonify({"orders": orders}), 200

if __name__ == '__main__':
        # Lancer le consumer dans un thread séparé
        consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
        consumer_thread.start()
        
        print(f"Service de commande démarré sur le port {PORT}")
        app.run(host='0.0.0.0', port=PORT, debug=False)