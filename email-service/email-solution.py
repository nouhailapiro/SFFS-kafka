from flask import Flask, jsonify
import json
import threading
from confluent_kafka import Consumer, Producer

app = Flask(__name__)

emails_sent = []

consumer_config = {
        "bootstrap.servers": "localhost:9094",
        "group.id": "email-service-group",
        "auto.offset.reset": "earliest"
}

producer_config = {
    "bootstrap.servers": "localhost:9094"
}

consumer = Consumer(consumer_config)
producer = Producer(producer_config)

def delivery_report(err, msg):
    if err:
        print(f"❌ Kafka delivery failed: {err}")
    else:
        print(f"✅ Message sent to {msg.topic()} [partition {msg.partition()}]")


def send_confirmation_email(message):
        user_id = message.get('user_id')
        order_id = message.get('order_id')
        
        email = {
                'to': f'user_{user_id}@example.com',
                'subject': f'Confirmation de commande #{order_id}',
                'body': f'Votre commande #{order_id} a été confirmée!'
        }
        
        emails_sent.append(email)
        print(f"Email envoyé: {email['subject']} à {email['to']}")

        # Produire un message dans le topic 'email-sent'
        email_event = {
                'user_id': user_id,
                'order_id': order_id,
                'email_to': email['to'],
                'subject': email['subject'],
                'status': 'sent'
        }
        
        producer.produce(
                topic="email-sent",
                value=json.dumps(email_event).encode("utf-8"),
                callback=delivery_report
        )
        producer.flush()

def kafka_consumer_loop():
        consumer.subscribe(["order-created"])
        print("Consumer démarré, en écoute sur 'order-created'...")
        
        while True:
                msg = consumer.poll(1.0)
                
                if msg is None:
                        continue
                if msg.error():
                        print(f"Erreur: {msg.error()}")
                        continue
                        
                try:
                        data = json.loads(msg.value().decode('utf-8'))
                        send_confirmation_email(data)
                except Exception as e:
                        print(f"Erreur de traitement: {e}")

@app.route('/emails', methods=['GET'])
def get_emails():
        return jsonify({"emails_sent": emails_sent}), 200

if __name__ == '__main__':
        consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
        consumer_thread.start()
        
        print("Service d'email démarré sur le port 8002")
        app.run(host='0.0.0.0', port=8002, debug=False)