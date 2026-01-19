#!/usr/bin/env python3
"""
🛒 Simulation Black Friday - Envoi direct à Kafka
Ce script envoie un grand nombre de messages directement à Kafka
pour simuler un pic de charge et observer le lag des consumers.
"""

from confluent_kafka import Producer
import json
import random
import time
import argparse

# Configuration
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

# Produits disponibles pour le Black Friday
PRODUCTS = [
    {"name": "iPhone 15 Pro", "price": 999},
    {"name": "MacBook Pro M3", "price": 1999},
    {"name": "AirPods Pro", "price": 249},
    {"name": "iPad Air", "price": 599},
    {"name": "Apple Watch", "price": 399},
    {"name": "PlayStation 5", "price": 499},
    {"name": "Samsung TV 65\"", "price": 899},
    {"name": "Nintendo Switch", "price": 299},
    {"name": "Xbox Series X", "price": 499},
    {"name": "Dyson V15", "price": 649},
]

# Statistiques
stats = {
    "sent": 0,
    "failed": 0,
}

def delivery_report(err, msg):
    """Callback appelé lors de la confirmation d'envoi"""
    if err:
        stats["failed"] += 1
    else:
        stats["sent"] += 1

def generate_random_cart():
    """Génère un panier aléatoire"""
    num_items = random.randint(1, 5)
    cart = []
    for _ in range(num_items):
        product = random.choice(PRODUCTS)
        cart.append({
            "name": product["name"],
            "price": product["price"],
            "quantity": random.randint(1, 3)
        })
    return cart

def run_simulation(num_messages, batch_size=100):
    """
    Envoie des messages directement à Kafka
    
    Args:
        num_messages: Nombre total de messages à envoyer
        batch_size: Nombre de messages par batch avant flush
    """
    print("=" * 70)
    print("🛒 SIMULATION BLACK FRIDAY - INJECTION DIRECTE KAFKA 🛒")
    print("=" * 70)
    print(f"📊 Configuration:")
    print(f"   - Nombre de messages à envoyer: {num_messages}")
    print(f"   - Topic cible: payment-successful")
    print(f"   - Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    print("=" * 70)
    print()
    
    producer_config = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "queue.buffering.max.messages": 100000,
        "queue.buffering.max.kbytes": 1048576,
        "batch.num.messages": 1000,
        "linger.ms": 5,
    }
    
    producer = Producer(producer_config)
    
    start_time = time.time()
    
    print("🚀 Début de l'injection des messages...")
    print()
    
    for i in range(1, num_messages + 1):
        event = {
            "user_id": i,
            "cart": generate_random_cart(),
            "timestamp": time.time()
        }
        
        producer.produce(
            topic="payment-successful",
            value=json.dumps(event).encode("utf-8"),
            callback=delivery_report
        )
        
        # Polling non-bloquant pour traiter les callbacks
        producer.poll(0)
        
        # Afficher la progression
        if i % 500 == 0:
            print(f"📤 {i}/{num_messages} messages envoyés...")
        
        # Flush périodique pour éviter le buffer overflow
        if i % batch_size == 0:
            producer.flush()
    
    # Flush final
    print()
    print("⏳ Flush final en cours...")
    producer.flush()
    
    total_time = time.time() - start_time
    
    # Afficher les résultats
    print()
    print("=" * 70)
    print("📊 RÉSULTATS DE L'INJECTION")
    print("=" * 70)
    print(f"✅ Messages envoyés: {stats['sent']}")
    print(f"❌ Échecs: {stats['failed']}")
    print(f"⏱️  Temps total: {total_time:.2f}s")
    print(f"📈 Débit: {stats['sent'] / total_time:.0f} messages/seconde")
    print()
    print("=" * 70)
    print("📋 PROCHAINES ÉTAPES")
    print("=" * 70)
    print()
    print("1. Vérifiez le LAG des consumers avec:")
    print("   python scripts/check_consumer_lag.py")
    print()
    print("2. Ou dans Kafka UI: http://localhost:8080")
    print("   → Topics → payment-successful → Consumers")
    print()
    print("💡 Si le lag est élevé, votre consumer ne suit pas la charge!")
    print("   → Solution: Augmenter les partitions + ajouter des consumers")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description="Simulation Black Friday - Injection Kafka")
    parser.add_argument(
        "-n", "--num-messages",
        type=int,
        default=1000,
        help="Nombre de messages à envoyer (défaut: 1000)"
    )
    parser.add_argument(
        "--intense",
        action="store_true",
        help="Mode intense: 5000 messages"
    )
    parser.add_argument(
        "--extreme",
        action="store_true",
        help="Mode extrême: 10000 messages"
    )
    
    args = parser.parse_args()
    
    if args.extreme:
        run_simulation(10000)
    elif args.intense:
        run_simulation(5000)
    else:
        run_simulation(args.num_messages)

if __name__ == "__main__":
    main()
