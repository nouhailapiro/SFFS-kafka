from flask import Flask, request, jsonify
import time
import json
# TODO Importer le Producer

app = Flask(__name__)

# TODO Créer la configuration du producer

# TODO Créer l'instance du producer
        
@app.route('/payment', methods=['POST'])
def process_payment():
    data = request.get_json()
    cart = data.get('cart')
    user_id = data.get('user_id')
    
    # Simulation du traitement du paiement
    print(f"Traitement du paiement pour l'utilisateur {user_id}")
    print(f"Panier: {cart}")
    
    # TODO Créer l'événement à envoyer
  

    # TODO Envoyer le message au topic 'payment-successful'
    
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
    print("Service de paiement démarré sur le port 8000")
    app.run(host='0.0.0.0', port=8000, debug=False)