from flask import Flask, jsonify
import json

app = Flask(__name__)

# Stockage en mémoire des commandes
orders = []

def process_payment_event(message):
    """
    Traite l'événement de paiement réussi
    """
    user_id = message.get('user_id')
    cart = message.get('cart')
    
    # Créer une nouvelle commande
    order = {
        'order_id': len(orders) + 1,
        'user_id': user_id,
        'items': cart,
        'status': 'confirmed'
    }
    
    orders.append(order)
    print(f"📦 Nouvelle commande créée: {order}")
    
    # TODO: Intégration Kafka ici
    # Le producteur enverra un message au topic 'order-created'

@app.route('/orders', methods=['GET'])
def get_orders():
    return jsonify({"orders": orders}), 200

def kafka_consumer_loop():
    """
    TODO: Intégration Kafka Consumer ici
    Le consommateur écoutera le topic 'payment-successful'
    et appellera process_payment_event() pour chaque message
    """
    #TODO: Partie 5: prendre en compte les messages empoisonnés

def send_to_dlq(message, error_reason):
    """
    TODO: Partie 5: Envoyer un message dans la Dead Letter Queue
    """

# Partie 5 : fonction de détection de caractères spéciaux 
def contains_special_chars(text):
    """ 
    TODO: Partie 5 : Completer la fonction pour detecter les caracteres speciaux
    """

if __name__ == '__main__':
    # Lancer le consumer dans un thread séparé
    # TODO: enlever les commentaires une fois la partie consumer implémentée
    # consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
    # consumer_thread.start()

    print("🚀 Service de commande démarré sur le port 8001")
    print("⏳ En attente d'événements de paiement...")
    app.run(host='0.0.0.0', port=8001, debug=False)