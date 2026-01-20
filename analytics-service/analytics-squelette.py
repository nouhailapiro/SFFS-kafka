from flask import Flask, jsonify
import json
import threading
import time

app = Flask(__name__)

# Statistiques en mémoire
analytics = {
    'total_payments': 0,
    'total_orders': 0,
    'total_emails': 0,
    'total_revenue': 0,
    'users': set(),
    'last_updated': None
}

# TODO Partie 2.4 et 6: Importer Consumer depuis confluent_kafka
# from confluent_kafka import Consumer

# TODO Partie 2.4: Créer la configuration du consumer
# La configuration doit contenir:
# - bootstrap.servers: localhost:9094
# - group.id: analytics-service-group
# - auto.offset.reset: earliest
# - enable.auto.commit: True
# consumer_config = { ... }

# TODO Partie 2.4: Créer l'instance du consumer
# consumer = Consumer(consumer_config)

def track_payment(message):
    """
    Enregistre les statistiques de paiement
    TODO Partie 6: Calculer le revenue total du panier
    """
    user_id = message.get('user_id')
    cart = message.get('cart', [])
    
    # Incrementer le compteur des commandes "total_payments"
    # analytics[...] ...

    # ajouter user_id à analytics['users']
    #analytics['users']....
    
    # TODO Partie 2.4: Calculer le total du panier
    # Parcourir cart et summ les (price * quantity) pour chaque item
    # total = sum(item.get('price', 0) * item.get('quantity', 1) for item in cart)
    # Puis ajouter à analytics['total_revenue']
    
    print(f"📊 [Payment] Paiement enregistré pour l'utilisateur {user_id}")

def track_order(message):
    """
    Enregistre les statistiques de commande
    """
    order_id = message.get('order_id')
    # Incrementer le compteur des commandes "total_orders"
    # analytics[...] ...
    
    print(f"📊 [Order] Commande enregistrée: #{order_id}")

def track_email(message):
    """
    Enregistre les statistiques d'email
    """
    order_id = message.get('order_id')
    email_to = message.get('email_to')
    # Incrementer le compteur des commandes "total_emails"
    # analytics[...] ...
    
    print(f"📊 [Email] Email enregistré: {email_to} pour commande #{order_id}")

@app.route('/analytics', methods=['GET'])
def get_analytics():
    """
    Retourne les statistiques en temps réel
    """
    stats = analytics.copy()
    stats['unique_users'] = len(analytics['users'])
    stats['users'] = list(analytics['users'])
    
    return jsonify(stats), 200

def kafka_consumer_loop():
    """
    TODO Partie 2.4: Boucle de consommation multi-topique
    - S'abonner à 3 topics: 'payment-successful', 'order-created', 'email-sent'
    - Écouter les messages
    - Vérifier le topic du message reçu
    - Router vers la fonction appropriée (track_payment, track_order, track_email)
    - Gérer les erreurs
    
    Étapes:
    1. consumer.subscribe(["payment-successful", "order-created", "email-sent"])
    2. Boucle infinie: msg = consumer.poll(1.0)
    3. Vérifier si msg is None, continuer
    4. Vérifier si msg.error(), logger et continuer
    5. Décoder: data = json.loads(msg.value().decode('utf-8'))
    6. Router par topic:
       - Si msg.topic() == "payment-successful": appeler track_payment(data)
       - Si msg.topic() == "order-created": appeler track_order(data)
       - Si msg.topic() == "email-sent": appeler track_email(data)
    7. Gérer les exceptions json.JSONDecodeError et autres exceptions
    """
    # TODO Partie 2.4: Implémenter la boucle
    # S'abonner à plusieurs topics (à completer)
    # consumer.subscribe([...])
    print("🎧 Consumer démarré, écoute sur 3 topics:")
    print("   - payment-successful")
    print("   - order-created")
    print("   - email-sent")
    
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                print(f"❌ Consumer error: {msg.error()}")
                continue
            
            # Décoder le message
            try:
                message_value = json.loads(msg.value().decode('utf-8'))
                topic = msg.topic()
                
                print(f"📨 Message reçu de '{topic}'")
                
                # Router vers la bonne fonction selon le topic
                if topic == "payment-successful":
                    track_payment(message_value)
                # elif topic == "order-created":
                    # router vers track_order
                # elif topic == "email-sent":
                    # router vers track_email
                # else:
                    #print(f"⚠️ Topic inconnu: {topic}")

            # décommenter une fois la boucle implémentée
            except json.JSONDecodeError as e:
                print(f"❌ Erreur de décodage JSON: {e}")
            except Exception as e:
                print(f"❌ Erreur lors du traitement: {e}")

    except KeyboardInterrupt:
        print("🛑 Arrêt du consumer...")
    finally:
        consumer.close()

if __name__ == '__main__':
    # TODO Partie 2.4: Décommenter une fois la boucle de consumer implémentée
    # consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
    # consumer_thread.start()

    print("🚀 Service d'analytics démarré sur le port 8003")
    print("⏳ En attente d'événements...")
    app.run(host='0.0.0.0', port=8003, debug=False)