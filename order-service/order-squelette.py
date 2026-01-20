import time
import os
from flask import Flask, jsonify
import json
import threading
import re
# TODO Partie 2.2.1: Importer les modules nécessaires

app = Flask(__name__)

# Port configurable via variable d'environnement (pour lancer plusieurs instances)
PORT = int(os.environ.get('PORT', 8001))
INSTANCE_ID = os.environ.get('INSTANCE_ID', '1')

# Stockage en mémoire des commandes
orders = []

# TODO Partie 2.2.2: Créer la configuration et l'instance du consumer

# TODO Partie 2.2.5: Créer la configuration du producer
# producer_config = { ... }

# TODO Partie 2.2.5: Créer l'instance du producer


def process_payment_event(message):
    """
    Traite l'événement de paiement réussi
    TODO Partie 3.2: Ajouter un délai time.sleep(0.1) pour simuler un traitement lent
    """
    user_id = message.get('user_id')
    cart = message.get('cart')
    
    # TODO Partie 3.2: Ajouter un délai de traitement réaliste (ex: time.sleep(0.1))
    
    # Créer une nouvelle commande
    order = {
        'order_id': len(orders) + 1,
        'user_id': user_id,
        'items': cart,
        'status': 'confirmed'
    }
    orders.append(order)

    print(f"📦 [Instance #{INSTANCE_ID}] Nouvelle commande créée: {order}")
    
    # TODO Partie 2.2.5: Produire un message au topic 'order-created'
    # Le message doit contenir les données de la commande (order)
    # Utilisez producer.produce() et producer.flush()
    # topic doit être "order-created"
    # value doit être json.dumps(order).encode("utf-8")
    # callback doit être delivery_report


# TODO Partie 2.2.3 :Implémenter la boucle du consumer (lecture et décodage)

def send_to_dlq(message, error_reason):
    """
    TODO Partie 5: Envoyer un message dans la Dead Letter Queue
    Vous devez:
    - Créer un dictionnaire dlq_message avec:
      - original_message: le message original
      - error: la raison de l'erreur
      - timestamp: time.time()
    - Produire ce message dans le topic 'dlq-payment'
    - Utiliser producer.produce() et producer.poll(0)
    """
    # dlq_message = ...
    # producer.produce(...) dans le topic "dlq-payment"
    # producer.poll(0) 
    
    print(f"Message envoyé à la DLQ: {error_reason}")

# TODO Partie 5: Fonction de détection de caractères spéciaux 
def contains_special_chars(text):
    """ 
    Détecte les caractères potentiellement malveillants
    """
    return bool(re.search(r"[<>'\"%;()&+]", text))

@app.route('/orders', methods=['GET'])
def get_orders():
    """Retourne la liste de toutes les commandes"""
    return jsonify({"orders": orders}), 200



@app.errorhandler(Exception)
def handle_error(error):
    return jsonify({"error": str(error)}), 500

if __name__ == '__main__':
    # TODO Partie 2.2.3: Décommenter une fois la boucle de consumer implémentée
    # consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
    # consumer_thread.start()

    print(f"🚀 Service de commande Instance #{INSTANCE_ID} démarré sur le port {PORT}")
    print("⏳ En attente d'événements de paiement...")
    app.run(host='0.0.0.0', port=PORT, debug=False)