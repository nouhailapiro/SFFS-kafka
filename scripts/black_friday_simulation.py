#!/usr/bin/env python3
"""
🛒 Simulation Black Friday - Script de charge
Ce script simule un afflux massif de commandes pendant le Black Friday.
"""

import requests
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import argparse

# Configuration
PAYMENT_SERVICE_URL = "http://localhost:8000/payment"

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
    "success": 0,
    "failed": 0,
    "total_time": 0,
    "errors": []
}
stats_lock = threading.Lock()

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

def send_payment_request(user_id):
    """Envoie une requête de paiement"""
    cart = generate_random_cart()
    payload = {
        "user_id": user_id,
        "cart": cart
    }
    
    start_time = time.time()
    try:
        response = requests.post(PAYMENT_SERVICE_URL, json=payload, timeout=30)
        elapsed = time.time() - start_time
        
        with stats_lock:
            if response.status_code == 200:
                stats["success"] += 1
                stats["total_time"] += elapsed
            else:
                stats["failed"] += 1
                stats["errors"].append(f"User {user_id}: HTTP {response.status_code}")
                
        return response.status_code == 200
        
    except requests.exceptions.Timeout:
        with stats_lock:
            stats["failed"] += 1
            stats["errors"].append(f"User {user_id}: Timeout")
        return False
    except requests.exceptions.ConnectionError:
        with stats_lock:
            stats["failed"] += 1
            stats["errors"].append(f"User {user_id}: Connection Error")
        return False
    except Exception as e:
        with stats_lock:
            stats["failed"] += 1
            stats["errors"].append(f"User {user_id}: {str(e)}")
        return False

def run_simulation(num_users, concurrent_users, delay_between_batches=0.1):
    """
    Lance la simulation du Black Friday
    
    Args:
        num_users: Nombre total de commandes à envoyer
        concurrent_users: Nombre de requêtes simultanées
        delay_between_batches: Délai entre chaque batch de requêtes
    """
    print("=" * 60)
    print("🛒 SIMULATION BLACK FRIDAY 🛒")
    print("=" * 60)
    print(f"📊 Configuration:")
    print(f"   - Nombre total de commandes: {num_users}")
    print(f"   - Requêtes simultanées: {concurrent_users}")
    print(f"   - URL du service de paiement: {PAYMENT_SERVICE_URL}")
    print("=" * 60)
    print()
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = []
        for user_id in range(1, num_users + 1):
            future = executor.submit(send_payment_request, user_id)
            futures.append(future)
            
            # Afficher la progression
            if user_id % 10 == 0:
                print(f"📤 {user_id}/{num_users} requêtes envoyées...")
            
            # Petit délai pour éviter de tout envoyer d'un coup
            if user_id % concurrent_users == 0:
                time.sleep(delay_between_batches)
        
        # Attendre toutes les réponses
        for future in futures:
            future.result()
    
    total_time = time.time() - start_time
    
    # Afficher les résultats
    print()
    print("=" * 60)
    print("📊 RÉSULTATS DE LA SIMULATION")
    print("=" * 60)
    print(f"✅ Succès: {stats['success']}")
    print(f"❌ Échecs: {stats['failed']}")
    print(f"⏱️  Temps total: {total_time:.2f}s")
    
    if stats['success'] > 0:
        avg_time = stats['total_time'] / stats['success']
        print(f"⏱️  Temps moyen par requête: {avg_time:.2f}s")
        print(f"📈 Débit: {stats['success'] / total_time:.2f} requêtes/seconde")
    
    if stats['failed'] > 0:
        print()
        print("⚠️  Dernières erreurs:")
        for error in stats['errors'][-5:]:
            print(f"   - {error}")
    
    print("=" * 60)
    
    # Vérifier si l'infrastructure a tenu
    success_rate = (stats['success'] / num_users) * 100 if num_users > 0 else 0
    
    if success_rate < 80:
        print()
        print("🔥 ALERTE: Le système n'a pas tenu la charge!")
        print("💡 Il est temps d'améliorer l'infrastructure avec Kafka:")
        print("   - Augmenter le nombre de partitions")
        print("   - Ajouter des consumer groups")
        print("   - Configurer la réplication")
    elif success_rate < 95:
        print()
        print("⚠️  ATTENTION: Des pertes ont été détectées!")
        print("💡 Considérez l'optimisation de votre configuration Kafka.")
    else:
        print()
        print("🎉 SUCCÈS: Le système a bien géré la charge!")

def main():
    parser = argparse.ArgumentParser(description="Simulation Black Friday")
    parser.add_argument(
        "-n", "--num-users",
        type=int,
        default=100,
        help="Nombre total de commandes à simuler (défaut: 100)"
    )
    parser.add_argument(
        "-c", "--concurrent",
        type=int,
        default=20,
        help="Nombre de requêtes simultanées (défaut: 20)"
    )
    parser.add_argument(
        "--intense",
        action="store_true",
        help="Mode intense: 500 commandes avec 50 requêtes simultanées"
    )
    
    args = parser.parse_args()
    
    if args.intense:
        run_simulation(500, 50, 0.05)
    else:
        run_simulation(args.num_users, args.concurrent)

if __name__ == "__main__":
    main()
