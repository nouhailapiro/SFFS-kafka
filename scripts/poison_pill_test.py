#!/usr/bin/env python3
"""
Test des messages empoisonnés (Poison Pills)
Ce script envoie des messages malformés pour tester la robustesse du système.
"""

from confluent_kafka import Producer
import json
import time

producer_config = {
    "bootstrap.servers": "localhost:9094"
}

producer = Producer(producer_config)

def delivery_report(err, msg):
    if err:
        print(f"Échec: {err}")
    else:
        print(f"Message envoyé au topic {msg.topic()}")

# Messages empoisonnés à tester
POISON_PILLS = [
    # 1. JSON invalide
    {
        "name": "JSON invalide",
        "data": "{ invalid json :",
        "topic": "payment-successful"
    },
    # 2. Champs manquants
    {
        "name": "Champs manquants (pas de user_id)",
        "data": json.dumps({"cart": [{"name": "Test", "price": 10}]}),
        "topic": "payment-successful"
    },
    # 3. Types incorrects
    {
        "name": "Type incorrect (user_id = string au lieu de int)",
        "data": json.dumps({"user_id": "not_a_number", "cart": "not_a_list"}),
        "topic": "payment-successful"
    },
    # 4. Valeurs nulles
    {
        "name": "Valeurs nulles",
        "data": json.dumps({"user_id": None, "cart": None}),
        "topic": "payment-successful"
    },
    # 5. Données vides
    {
        "name": "Objet vide",
        "data": json.dumps({}),
        "topic": "payment-successful"
    },
    # 6. Valeurs négatives
    {
        "name": "Prix négatif",
        "data": json.dumps({
            "user_id": 999,
            "cart": [{"name": "Arnaque", "price": -1000, "quantity": 1}]
        }),
        "topic": "payment-successful"
    },
    # 7. Message trop long
    {
        "name": "Message très long",
        "data": json.dumps({
            "user_id": 999,
            "cart": [{"name": "X" * 10000, "price": 10, "quantity": 1}]
        }),
        "topic": "payment-successful"
    },
    # 8. Injection de caractères spéciaux
    {
        "name": "Caractères spéciaux/injection",
        "data": json.dumps({
            "user_id": "'; DROP TABLE users; --",
            "cart": [{"name": "<script>alert('xss')</script>", "price": 10}]
        }),
        "topic": "payment-successful"
    },
]

def send_poison_pills():
    """Envoie tous les messages empoisonnés"""
    print("=" * 60)
    print("TEST DES MESSAGES EMPOISONNÉS")
    print("=" * 60)
    print()
    print("Ce script va envoyer des messages malformés pour tester")
    print("la robustesse de votre système de traitement Kafka.")
    print()
    print("Observez comment vos consumers réagissent!")
    print("=" * 60)
    print()
    
    for i, poison in enumerate(POISON_PILLS, 1):
        print(f"[{i}/{len(POISON_PILLS)}] Envoi: {poison['name']}")
        
        try:
            producer.produce(
                topic=poison['topic'],
                value=poison['data'].encode('utf-8') if isinstance(poison['data'], str) else poison['data'],
                callback=delivery_report
            )
            producer.poll(0)
        except Exception as e:
            print(f"   Erreur lors de l'envoi: {e}")
        
        time.sleep(0.5)  # Petit délai pour voir les effets
    
    # Attendre que tous les messages soient envoyés
    producer.flush()
    
    print()
    print("=" * 60)
    print("Tous les messages empoisonnés ont été envoyés!")
    print()
    print("Vérifiez maintenant:")
    print("   1. Les logs de vos consumers")
    print("   2. Si le consumer a crashé ou continue de fonctionner")
    print("   3. Si les messages sont dans une Dead Letter Queue")
    print("   4. L'état du consumer group dans Kafka UI")
    print("=" * 60)

def send_single_poison(poison_type):
    """Envoie un seul type de message empoisonné"""
    if poison_type < 1 or poison_type > len(POISON_PILLS):
        print(f"Type invalide. Choisissez entre 1 et {len(POISON_PILLS)}")
        return
    
    poison = POISON_PILLS[poison_type - 1]
    print(f"📤 Envoi: {poison['name']}")
    
    producer.produce(
        topic=poison['topic'],
        value=poison['data'].encode('utf-8') if isinstance(poison['data'], str) else poison['data'],
        callback=delivery_report
    )
    producer.flush()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        try:
            poison_type = int(sys.argv[1])
            send_single_poison(poison_type)
        except ValueError:
            print("Usage: python poison_pill_test.py [numéro du poison 1-8]")
    else:
        send_poison_pills()
