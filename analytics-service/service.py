from flask import Flask, jsonify
import json

app = Flask(__name__)

# Statistiques en mémoire
analytics = {
    'total_payments': 0,
    'total_orders': 0,
    'total_revenue': 0,
    'users': set()
}

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
    
    print(f"📊 Paiement enregistré: {total}€ pour l'utilisateur {user_id}")

def track_order(message):
    """
    Enregistre les statistiques de commande
    """
    order_id = message.get('order_id')
    
    analytics['total_orders'] += 1
    
    print(f"📊 Commande enregistrée: #{order_id}")

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

if __name__ == '__main__':
    print("🚀 Service d'analytics démarré sur le port 8003")
    print("⏳ En attente d'événements...")
    app.run(host='0.0.0.0', port=8003, debug=False)