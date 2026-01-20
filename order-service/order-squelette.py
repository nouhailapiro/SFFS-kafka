import time
import os
from flask import Flask, jsonify
import json
import threading
import re

app = Flask(__name__)

# Port configurable via variable d'environnement (pour lancer plusieurs instances)
PORT = int(os.environ.get('PORT', 8001))
INSTANCE_ID = os.environ.get('INSTANCE_ID', '1')

# Stockage en mémoire des commandes
orders = []

# TODO Partie 2.2: Importer Consumer et Producer depuis confluent_kafka
# from confluent_kafka import Consumer, Producer

# TODO Partie 2.2: Créer la configuration du consumer
# La configuration doit contenir:
# - bootstrap.servers: localhost:9094
# - group.id: order-service-group
# - auto.offset.reset: earliest
#consumer_config = {
#       "bootstrap.servers": "localhost:9094",
#       "group.id": "order-service-group",
#       "auto.offset.reset": "earliest"
#}

# TODO Partie 2.2: Créer la configuration du producer
# producer_config = { ... }

# TODO Partie 2.2: Créer les instances du consumer et producer
# consumer = Consumer(consumer_config)
# producer = Producer(producer_config)

def delivery_report(err, msg):
    """Callback pour confirmer l'envoi du message Kafka"""
    if err:
        print(f"❌ Échec envoi: {err}")
    else:
        print(f"✅ Message envoyé à {msg.topic()} [partition {msg.partition()}]")

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
        # order_id doit être unique, utilisez len(orders) + 1
        'order_id': 0, # À remplacer,
        'user_id': user_id,
        'items': cart,
        'status': 'confirmed'
    }
    # Ajouter la commande à la liste des commandes (orders)

    print(f"📦 [Instance #{INSTANCE_ID}] Nouvelle commande créée: {order}")
    
    # TODO Partie 2.2: Produire un message au topic 'order-created'
    # Le message doit contenir les données de la commande (order)
    # Utilisez producer.produce() et producer.poll(0)
    # topic doit être "order-created"
    # value doit être json.dumps(order).encode("utf-8")
    # callback doit être delivery_report


@app.route('/orders', methods=['GET'])
def get_orders():
    """Retourne la liste de toutes les commandes"""
    return jsonify({"orders": orders}), 200

def kafka_consumer_loop():
    """
    TODO Partie 2.2: Boucle de consommation Kafka
    - S'abonner au topic 'payment-successful'
    - Écouter les messages
    - Parser le JSON
    - Appeler process_payment_event() pour chaque message
    - Gérer les erreurs
    
    TODO Partie 5: Implémenter la gestion des messages empoisonnés
    - Attraper les exceptions json.JSONDecodeError et ValueError
    - Envoyer les messages en erreur à send_to_dlq()
    - Continuer le traitement des autres messages
    """


    # TODO Partie 2.2: Implémenter la boucle
    # consumer.subscribe(["payment-successful"])
    # print(f" [Instance #{INSTANCE_ID}] Consumer démarré, en écoute sur 'payment-successful'...")
    # while True:
    #     msg = consumer.poll(1.0)
    #     ...
    # consumer.subscribe(["payment-successful"])
    print("Consumer démarré, en écoute sur 'payment-successful'...")
    while True:
        #msg = (...)

        if msg is None:
            continue
        if msg.error():
            print(f"Erreur: {msg.error()}")
            continue
        # ram_value prendre la valeur du message
        # raw_value = ...

        try:
            # 1. Parsing JSON
            data = json.loads(raw_value.decode('utf-8'))

            #TODO Partie 5: Implémenter la gestion des messages empoisonnés
            # 2. Validation des champs requis
            # verifier que user_id est un int ou str
            if True: # À remplacer
                raise ValueError("user_id invalide")
            # verifier que cart est une liste
            if True:
                raise ValueError("cart doit être une liste")
            # verifier que chaque item dans cart a un name de type str
            if True:
                raise ValueError("Le nom de chaque item doit être une chaîne de caractères")
            # verifier que chaque item dans cart a un price de type int/float > 0
            if True:
                raise ValueError("Le prix de chaque item doit être un nombre positif")
            # verifier que les chaînes de caractères ne sont pas trop longues
            if True:
                raise ValueError("Le nom de l'item est trop long")
            # verifier qu'il n'y a pas de caractères spéciaux dans user_id et name
            # utiliser la fonction contains_special_chars()
            if True:
                raise ValueError("Caractères spéciaux détectés dans user_id")
            for item in data.get('cart', []):
                # verifier qu'il n'y a pas de caractères spéciaux dans name
                if True:
                    raise ValueError("Caractères spéciaux détectés dans le nom de l'item")
            # 3. Traitement
            process_payment_event(data)

        except json.JSONDecodeError as e:
            print(f"JSON invalide: {e}")
            # envoyer le message à la DLQ
            # appeler la fonction send_to_dlq avec le message original et la raison de l'erreur

        except ValueError as e:
            print(f"Validation échouée: {e}")
            # envoyer le message à la DLQ
            # appeler la fonction send_to_dlq avec le message original et la raison de l'erreur
        except Exception as e:
            print(f"Erreur inattendue: {e}")
            # envoyer le message à la DLQ
            # appeler la fonction send_to_dlq avec le message original et la raison de l'erreur

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

@app.errorhandler(Exception)
def handle_error(error):
    return jsonify({"error": str(error)}), 500

if __name__ == '__main__':
    # TODO Partie 2.2: Décommenter une fois la boucle de consumer implémentée
    # consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
    # consumer_thread.start()

    print(f"🚀 Service de commande Instance #{INSTANCE_ID} démarré sur le port {PORT}")
    print("⏳ En attente d'événements de paiement...")
    app.run(host='0.0.0.0', port=PORT, debug=False)