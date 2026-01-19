from flask import Flask, jsonify
import json

app = Flask(__name__)

# Historique des emails envoyés
emails_sent = []

def send_confirmation_email(message):
    """
    Envoie un email de confirmation de commande
    """
    user_id = message.get('user_id')
    order_id = message.get('order_id')
    
    # Simulation de l'envoi d'email
    email = {
        'to': f'user_{user_id}@example.com',
        'subject': f'Confirmation de commande #{order_id}',
        'body': f'Votre commande #{order_id} a été confirmée avec succès!'
    }
    
    emails_sent.append(email)
    print(f"📧 Email envoyé: {email['subject']} à {email['to']}")

@app.route('/emails', methods=['GET'])
def get_emails():
    return jsonify({"emails_sent": emails_sent}), 200

# TODO: Intégration Kafka Consumer ici
# Le consommateur écoutera le topic 'order-created'
# et appellera send_confirmation_email() pour chaque message

if __name__ == '__main__':
    print("🚀 Service d'email démarré sur le port 8002")
    print("⏳ En attente d'événements de commande...")
    app.run(host='0.0.0.0', port=8002, debug=False)