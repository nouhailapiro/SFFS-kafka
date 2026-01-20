from flask import Flask, jsonify
import json
import threading
from confluent_kafka import Consumer

app = Flask(__name__)

# Statistiques en mémoire
analytics = {
    'total_payments': 0,
    'total_orders': 0,
    'total_emails': 0,
    'total_revenue': 0,
    'users': set()
}

# Configuration du consumer
consumer_config = {
    "bootstrap.servers": "localhost:9094",
    "group.id": "analytics-service-group",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": True
}

consumer = Consumer(consumer_config)

def track_payment(message):
    """
    Enregistre les statistiques de paiement
    """
    user_id = message.get('user_id')
    cart = message.get('cart', [])
    
    analytics['total_payments'] += 1
    analytics['users'].add(user_id)
    
    # Calculer le total du panier (simulation)
    total = sum(item.get('price', 0) * item.get('quantity', 1) for item in cart)
    analytics['total_revenue'] += total
    
    print(f"Paiement enregistré: {total}€ pour l'utilisateur {user_id}")

def track_order(message):
    """
    Enregistre les statistiques de commande
    """
    order_id = message.get('order_id')
    
    analytics['total_orders'] += 1
    
    print(f"Commande enregistrée: #{order_id}")

def track_email(message):
    """
    Enregistre les statistiques d'email
    """
    order_id = message.get('order_id')
    email_to = message.get('email_to')
    
    analytics['total_emails'] += 1
    
    print(f"Email enregistré: {email_to} pour commande #{order_id}")


@app.route('/analytics', methods=['GET'])
def get_analytics():
    stats = analytics.copy()
    stats['unique_users'] = len(analytics['users'])
    stats['users'] = list(analytics['users'])
    
    return jsonify(stats), 200

# TODO: Intégration Kafka Consumer ici
# Le consommateur écoutera les topics:
# - 'payment-successful' pour track_payment()
# - 'order-created' pour track_order()
# - 'email-sent' pour les emails
def kafka_consumer_loop():
    """
    Thread qui consomme les messages de plusieurs topics
    """
    # S'abonner à plusieurs topics
    consumer.subscribe(["payment-successful", "order-created", "email-sent"])
    print("Consumer démarré, écoute sur 3 topics:")
    print("   - payment-successful")
    print("   - order-created")
    print("   - email-sent")
    
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue
            
            # Décoder le message
            try:
                message_value = json.loads(msg.value().decode('utf-8'))
                topic = msg.topic()
                
                print(f"Message reçu de '{topic}'")
                
                # Router vers la bonne fonction selon le topic
                if topic == "payment-successful":
                    track_payment(message_value)
                elif topic == "order-created":
                    track_order(message_value)
                elif topic == "email-sent":
                    track_email(message_value)
                else:
                    print(f"Topic inconnu: {topic}")
                    
            except json.JSONDecodeError as e:
                print(f"Erreur de décodage JSON: {e}")
            except Exception as e:
                print(f"Erreur lors du traitement: {e}")
                
    except KeyboardInterrupt:
        print("🛑 Arrêt du consumer...")
    finally:
        consumer.close()

if __name__ == '__main__':
    # Démarrer le consumer Kafka dans un thread séparé
    consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
    consumer_thread.start()

    print("Service d'analytics démarré sur le port 8003")
    print("En attente d'événements...")
    app.run(host='0.0.0.0', port=8003, debug=False)