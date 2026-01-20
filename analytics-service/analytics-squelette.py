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
    
    analytics['total_payments'] += 1
    analytics['users'].add(user_id)
    
    # TODO Partie 6: Calculer le total du panier
    # Parcourir cart et summ les (price * quantity) pour chaque item
    # total = sum(item.get('price', 0) * item.get('quantity', 1) for item in cart)
    # Puis ajouter à analytics['total_revenue']
    
    print(f"📊 [Payment] Paiement enregistré pour l'utilisateur {user_id}")

def track_order(message):
    """
    Enregistre les statistiques de commande
    """
    order_id = message.get('order_id')
    
    analytics['total_orders'] += 1
    
    print(f"📊 [Order] Commande enregistrée: #{order_id}")

def track_email(message):
    """
    Enregistre les statistiques d'email
    """
    order_id = message.get('order_id')
    email_to = message.get('email_to')
    
    analytics['total_emails'] += 1
    
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

if __name__ == '__main__':
    # TODO Partie 2.4: Décommenter une fois la boucle de consumer implémentée
    # consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
    # consumer_thread.start()

    print("🚀 Service d'analytics démarré sur le port 8003")
    print("⏳ En attente d'événements...")
    app.run(host='0.0.0.0', port=8003, debug=False)