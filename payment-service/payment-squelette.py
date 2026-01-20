from flask import Flask, request, jsonify
import time
import json

app = Flask(__name__)

# TODO Partie 2.1: Importer le Producer depuis confluent_kafka
# Référence: https://github.com/confluentinc/confluent-kafka-python
# Vous devez importer Producer depuis confluent_kafka

# TODO Partie 2.1: Créer la configuration du producer
# La configuration doit contenir bootstrap.servers pointant vers localhost:9094
# producer_config = {
#    "bootstrap.servers": "localhost:9094"
#}

# TODO Partie 2.1: Créer l'instance du producer
# producer = ...

def delivery_report(err, msg):
    """Callback pour confirmer l'envoi du message Kafka"""
    if err:
        print(f"❌ Kafka delivery failed: {err}")
    else:
        print(f"✅ Message sent to topic {msg.topic()} partition[{msg.partition()}]")
        
@app.route('/payment', methods=['POST'])
def process_payment():
    data = request.get_json()
    cart = data.get('cart')
    user_id = data.get('user_id')
    
    # Simulation du traitement du paiement
    print(f"💳 Traitement du paiement pour l'utilisateur {user_id}")
    print(f"Panier: {cart}")
    
    # TODO Partie 2.1: Créer l'événement à envoyer
    # L'événement doit être un dictionnaire avec:
    # - user_id
    # - cart
    # - timestamp (utiliser time.time())
    # event = {
    #     "user_id": user_id,
    #     "cart": cart,
    #     "timestamp": time.time()
    # }

    # TODO Partie 2.1: Envoyer le message au topic 'payment-successful'
    # Utilisez producer.produce() avec:
    # - topic: "payment-successful"
    # - value: json.dumps(event).encode("utf-8")
    # - callback: delivery_report
    # N'oubliez pas d'appeler producer.flush() pour s'assurer que le message est envoyé
    
    # Simulation d'un délai de traitement
    time.sleep(2)
    
    return jsonify({
        "status": "success",
        "message": "Paiement effectué avec succès",
        "user_id": user_id,
        "cart": cart
    }), 200

@app.errorhandler(Exception)
def handle_error(error):
    return jsonify({"error": str(error)}), 500

if __name__ == '__main__':
    print("🚀 Service de paiement démarré sur le port 8000")
    app.run(host='0.0.0.0', port=8000, debug=False)