from flask import Flask, jsonify
import json
import threading
# TODO Partie 2.3.1: Importer Consumer et Producer depuis confluent_kafka

app = Flask(__name__)

# Historique des emails envoyés
emails_sent = []

# TODO Partie 2.3.1: Importer Consumer et Producer depuis confluent_kafka


# TODO Partie 2.3.2: Créer la configuration du consumer et du producer
# consumer_config = { ... }
# producer_config = { ... }

# TODO Partie 2.3.2: Créer les instances du consumer et producer


def delivery_report(err, msg):
    """Callback pour confirmer l'envoi du message Kafka"""
    if err:
        print(f"Kafka delivery failed: {err}")
    else:
        print(f"Message sent to {msg.topic()} [partition {msg.partition()}]")

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

    # TODO Partie 2.3.3: Produire un message au topic 'email-sent'
    # Le message doit contenir:
    # - user_id
    # - order_id
    # - email_to (l'adresse email)
    # - subject
    # - status: 'sent'
    # Utilisez producer.produce() et producer.flush()
    # email_event = 
    # producer.produce(...)
    # producer.flush()

@app.route('/emails', methods=['GET'])
def get_emails():
    """Retourne la liste de tous les emails envoyés"""
    return jsonify({"emails_sent": emails_sent}), 200

def kafka_consumer_loop():
    """
    TODO Partie 2.3.4: Boucle de consommation Kafka
    - S'abonner au topic 'order-created'
    - Écouter les messages
    - Parser le JSON
    - Appeler send_confirmation_email() pour chaque message
    """

    # consumer.subscribe() à order-created"
    # print(" Consumer démarré, en écoute sur 'order-created'...")

    while True:
        # msg = ...
        
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

if __name__ == '__main__':
    # TODO Partie 2.3.4: Décommenter une fois la boucle de consumer implémentée
    # consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
    # consumer_thread.start()

    print("Service d'email démarré sur le port 8002")
    print("En attente d'événements de commande...")
    app.run(host='0.0.0.0', port=8002, debug=False)