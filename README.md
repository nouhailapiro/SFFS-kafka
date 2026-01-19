# TP Kafka - Black Friday Challenge

## Contexte

Vous êtes développeur dans une startup e-commerce. Le **Black Friday** approche et votre plateforme doit gérer un pic de trafic 100x supérieur à la normale ! 

Actuellement, votre architecture est composée de 4 microservices :

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Payment   │ ──► │    Order    │ ──► │    Email    │     │  Analytics  │
│   Service   │     │   Service   │     │   Service   │     │   Service   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**Le problème:** Ces services communiquent de manière synchrone. Lors du Black Friday, si un service est surchargé, tout le système s'effondre ! 

**La solution:** Apache Kafka ! 

---

## Objectifs du TP

À la fin de ce TP, vous saurez :

- Créer et configurer des topics Kafka
- Implémenter des producers et consumers
- Configurer les partitions et la réplication
- Utiliser les consumer groups pour la scalabilité
- Gérer les messages empoisonnés (poison pills)
- Implémenter du streaming en temps réel

---

## Partie 0 : Installation et Setup

### 0.1 Cloner le projet

```bash
git clone https://github.com/nouhailapiro/SFFS-kafka
cd SFFS-kafka
```

### 0.2 Créer l'environnement virtuel

```bash
# Créer l'environnement
python -m venv venv

# L'activer
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 0.3 Lancer l'infrastructure Kafka

```bash
cd kafka
docker compose up -d
```

Vérifiez que tout fonctionne :
```bash
docker ps
```

Vous devriez voir 2 containers : `kafka` et `kafka-ui`

### 0.4 Accéder à Kafka UI

Ouvrez votre navigateur : **http://localhost:8080**

C'est votre tableau de bord pour visualiser Kafka !

---

## Partie 1 : Découverte de Kafka CLI

Avant de coder, familiarisons-nous avec les commandes Kafka.

### 1.1 Créer votre premier topic

```bash
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 \
    --create \
    --topic payment-successful \
    --partitions 1 \
    --replication-factor 1
```

**Vérification:** Allez sur Kafka UI et vérifiez que le topic existe.

### 1.2 Créer les autres topics

Créez les topics suivants avec la même commande :

| Topic | Description |
|-------|-------------|
| `order-created` | Événements de création de commande |
| `dlq-payment` | Dead Letter Queue pour les erreurs |

<details>
<summary>Solution</summary>

```bash
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 \
    --create --topic order-created --partitions 1 --replication-factor 1

docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 \
    --create --topic dlq-payment --partitions 1 --replication-factor 1
```
</details>

### 1.3 Lister les topics

```bash
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### 1.4 Tester avec la console

**Terminal 1 - Consumer:**
```bash
docker exec -it kafka kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic payment-successful \
    --from-beginning
```

**Terminal 2 - Producer:**
```bash
docker exec -it kafka kafka-console-producer \
    --bootstrap-server localhost:9092 \
    --topic payment-successful
```

Tapez un message et appuyez sur Entrée. Vous devriez le voir apparaître dans le Terminal 1 !

---

## Partie 2 : Intégration Kafka dans les Services

### 2.1 Le Service de Paiement (Producer)

**Objectif:** Modifier `payment-service/service.py` pour envoyer un message Kafka lorsqu'un paiement est effectué.

**TODO:**

1. Importer le Producer Kafka depuis `confluent_kafka`
2. Créer la configuration du producer
3. Créer une fonction `delivery_report` pour logger le résultat de l'envoi
4. Produire un message sur le topic `payment-successful` après traitement du paiement

<details>
<summary>Indices</summary>

```python
from confluent_kafka import Producer

producer_config = {
    "bootstrap.servers": "localhost:9092"
}

producer = Producer(producer_config)

# Pour envoyer un message :
producer.produce(
    topic="payment-successful",
    value=json.dumps(event).encode("utf-8"),
    callback=delivery_report
)
producer.flush()  # Attendre que le message soit envoyé
```
</details>

<details>
<summary>Solution complète</summary>

```python
from flask import Flask, request, jsonify
import time
import json
from confluent_kafka import Producer

app = Flask(__name__)

producer_config = {
    "bootstrap.servers": "localhost:9092"
}

producer = Producer(producer_config)

def delivery_report(err, msg):
    if err:
        print(f"❌ Kafka delivery failed: {err}")
    else:
        print(f"✅ Message sent to topic {msg.topic()} partition[{msg.partition()}]")

@app.route('/payment', methods=['POST'])
def process_payment():
    data = request.get_json()
    cart = data.get('cart')
    user_id = data.get('user_id')
    
    print(f"💳 Traitement du paiement pour l'utilisateur {user_id}")
    print(f"Panier: {cart}")
    
    # Créer l'événement à envoyer
    event = {
        "user_id": user_id,
        "cart": cart,
        "timestamp": time.time()
    }

    # Envoyer le message à Kafka
    producer.produce(
        topic="payment-successful",
        value=json.dumps(event).encode("utf-8"),
        callback=delivery_report
    )
    producer.flush()
    
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
```
</details>

**Lancez le service :**
```bash
python payment-service/service.py
```

**Dans un autre terminal, testez avec curl :**
```bash
curl -X POST http://localhost:8000/payment \
    -H "Content-Type: application/json" \
    -d '{"user_id": 1, "cart": [{"name": "iPhone", "price": 999, "quantity": 1}]}'
```

**Vérification:** Regardez le topic `payment-successful` dans Kafka UI. Vous devriez voir votre message !

### 2.2 Le Service de Commande (Consumer)

**Objectif:** Modifier `order-service/service.py` pour consommer les messages du topic `payment-successful`.

**TODO:**

1. Ajouter l'import du consumer Kafka
2. Créer la configuration du consumer
3. Implémenter la boucle de consommation
4. Produire un message sur `order-created` après traitement

<details>
<summary>Indices</summary>

```python
from confluent_kafka import Consumer, Producer

consumer_config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "order-service-group",
        "auto.offset.reset": "earliest"
}

consumer = Consumer(consumer_config)
consumer.subscribe(["payment-successful"])
```
</details>

<details>
<summary>Solution complète</summary>

```python
from flask import Flask, jsonify
import json
import threading
from confluent_kafka import Consumer, Producer

app = Flask(__name__)

orders = []

# Configuration Kafka
consumer_config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "order-service-group",
        "auto.offset.reset": "earliest"
}

producer_config = {
        "bootstrap.servers": "localhost:9092"
}

consumer = Consumer(consumer_config)
producer = Producer(producer_config)

def delivery_report(err, msg):
        if err:
                print(f"Échec envoi: {err}")
        else:
                print(f"Message envoyé à {msg.topic()}")

def process_payment_event(message):
        user_id = message.get('user_id')
        cart = message.get('cart')
        
        order = {
                'order_id': len(orders) + 1,
                'user_id': user_id,
                'items': cart,
                'status': 'confirmed'
        }
        
        orders.append(order)
        print(f"Nouvelle commande créée: {order}")
        
        # Produire l'événement order-created
        producer.produce(
                topic="order-created",
                value=json.dumps(order).encode("utf-8"),
                callback=delivery_report
        )
        producer.poll(0)

def kafka_consumer_loop():
        consumer.subscribe(["payment-successful"])
        print("Consumer démarré, en écoute sur 'payment-successful'...")
        
        while True:
                msg = consumer.poll(1.0)
                
                if msg is None:
                        continue
                if msg.error():
                        print(f"Erreur: {msg.error()}")
                        continue
                        
                try:
                        data = json.loads(msg.value().decode('utf-8'))
                        process_payment_event(data)
                except Exception as e:
                        print(f"Erreur de traitement: {e}")

@app.route('/orders', methods=['GET'])
def get_orders():
        return jsonify({"orders": orders}), 200

if __name__ == '__main__':
        # Lancer le consumer dans un thread séparé
        consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
        consumer_thread.start()
        
        print("Service de commande démarré sur le port 8001")
        app.run(host='0.0.0.0', port=8001, debug=False)
```
</details>

### 2.3 Le Service Email (Consumer)

**Objectif:** Modifier `email-service/service.py` pour consommer les messages du topic `order-created`.

Faites la même chose que pour le service de commande, mais en écoutant le topic `order-created`.

<details>
<summary>Solution complète</summary>

```python
from flask import Flask, jsonify
import json
import threading
from confluent_kafka import Consumer

app = Flask(__name__)

emails_sent = []

consumer_config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "email-service-group",
        "auto.offset.reset": "earliest"
}

consumer = Consumer(consumer_config)

def send_confirmation_email(message):
        user_id = message.get('user_id')
        order_id = message.get('order_id')
        
        email = {
                'to': f'user_{user_id}@example.com',
                'subject': f'Confirmation de commande #{order_id}',
                'body': f'Votre commande #{order_id} a été confirmée!'
        }
        
        emails_sent.append(email)
        print(f"Email envoyé: {email['subject']} à {email['to']}")

def kafka_consumer_loop():
        consumer.subscribe(["order-created"])
        print("Consumer démarré, en écoute sur 'order-created'...")
        
        while True:
                msg = consumer.poll(1.0)
                
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

@app.route('/emails', methods=['GET'])
def get_emails():
        return jsonify({"emails_sent": emails_sent}), 200

if __name__ == '__main__':
        consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
        consumer_thread.start()
        
        print("Service d'email démarré sur le port 8002")
        app.run(host='0.0.0.0', port=8002, debug=False)
```
</details>

### 2.4 Test de l'intégration

Lancez tous les services dans des terminaux séparés :

```bash
# Terminal 1
python payment-service/service.py

# Terminal 2
python order-service/service.py

# Terminal 3
python email-service/service.py
```

Envoyez un paiement :
```bash
curl -X POST http://localhost:8000/payment \
    -H "Content-Type: application/json" \
    -d '{"user_id": 42, "cart": [{"name": "MacBook", "price": 1999, "quantity": 1}]}'
```

**Vérification:** Vous devriez voir :
1. Le paiement traité (Terminal 1)
2. La commande créée (Terminal 2)
3. L'email envoyé (Terminal 3)

---

## Partie 3 : Simulation Black Friday (15 min)

### 3.1 Lancer la simulation

Maintenant, testons notre système sous charge !

```bash
python scripts/black_friday_simulation.py -n 50 -c 10
```

Observez ce qui se passe :
- Les services arrivent-ils à suivre ?
- Y a-t-il des erreurs ?
- Quel est le temps de réponse ?

### 3.2 Mode intense

```bash
python scripts/black_friday_simulation.py --intense
```

**Problème identifié:** Avec une seule partition et un seul consumer, le système ne tient pas la charge !

---

## Partie 4 : Optimisation avec les Partitions et Consumer Groups (20 min)

### 4.1 Comprendre les partitions

Les partitions permettent de paralléliser le traitement des messages.

```
                                        Topic: payment-successful
                ┌─────────────────────────────────────────┐
                │  Partition 0  │  Partition 1  │  Partition 2  │
                └───────┬───────┴───────┬───────┴───────┬───────┘
                                │               │               │
                                ▼               ▼               ▼
                     Consumer 1      Consumer 2      Consumer 3
```

### 4.2 Recréer les topics avec plus de partitions

```bash
# Supprimer les anciens topics
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 \
    --delete --topic payment-successful

docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 \
    --delete --topic order-created

# Recréer avec 3 partitions
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 \
    --create --topic payment-successful --partitions 3 --replication-factor 1

docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 \
    --create --topic order-created --partitions 3 --replication-factor 1
```

### 4.3 Lancer plusieurs instances du consumer

**Terminal 1:**
```bash
python order-service/service.py  # Port 8001
```

**Terminal 2:** (modifiez le port dans le code ou utilisez une variable d'env)
```bash
PORT=8011 python order-service/service.py
```

**Terminal 3:**
```bash
PORT=8012 python order-service/service.py
```

### 4.4 Vérifier la distribution

1. Allez sur Kafka UI : http://localhost:8080
2. Cliquez sur "Consumers" → "order-service-group"
3. Observez comment les partitions sont réparties entre les consumers

### 4.5 Relancer la simulation

```bash
python scripts/black_friday_simulation.py --intense
```

**Résultat attendu:** Meilleur débit et moins d'erreurs !

---

## Partie 5 : Gestion des Messages Empoisonnés (20 min)

### 5.1 Qu'est-ce qu'un message empoisonné ?

Un "poison pill" est un message malformé qui peut faire crasher votre consumer :
- JSON invalide
- Champs manquants
- Types incorrects
- Valeurs nulles

### 5.2 Tester les messages empoisonnés

```bash
python scripts/poison_pill_test.py
```

Observez les logs de vos consumers. Que se passe-t-il ?

### 5.3 Implémenter une gestion robuste

**Objectif:** Modifier le consumer pour :
1. Attraper les erreurs de parsing
2. Logger les erreurs
3. Envoyer les messages en erreur dans une Dead Letter Queue (DLQ)
4. Continuer le traitement des autres messages

<details>
<summary>Solution avec DLQ</summary>

```python
def kafka_consumer_loop():
        consumer.subscribe(["payment-successful"])
        
        while True:
                msg = consumer.poll(1.0)
                
                if msg is None:
                        continue
                if msg.error():
                        print(f"Erreur Kafka: {msg.error()}")
                        continue
                
                raw_value = msg.value()
                
                try:
                        # 1. Parsing JSON
                        data = json.loads(raw_value.decode('utf-8'))
                        
                        # 2. Validation des champs requis
                        if not isinstance(data.get('user_id'), (int, str)):
                                raise ValueError("user_id invalide")
                        if not isinstance(data.get('cart'), list):
                                raise ValueError("cart doit être une liste")
                        
                        # 3. Traitement
                        process_payment_event(data)
                        
                except json.JSONDecodeError as e:
                        print(f"JSON invalide: {e}")
                        send_to_dlq(raw_value, str(e))
                        
                except ValueError as e:
                        print(f"Validation échouée: {e}")
                        send_to_dlq(raw_value, str(e))
                        
                except Exception as e:
                        print(f"Erreur inattendue: {e}")
                        send_to_dlq(raw_value, str(e))

def send_to_dlq(message, error_reason):
        """Envoie un message dans la Dead Letter Queue"""
        dlq_message = {
                "original_message": message.decode('utf-8') if isinstance(message, bytes) else str(message),
                "error": error_reason,
                "timestamp": time.time()
        }
        
        producer.produce(
                topic="dlq-payment",
                value=json.dumps(dlq_message).encode('utf-8'),
                callback=delivery_report
        )
        producer.poll(0)
        print(f"Message envoyé à la DLQ: {error_reason}")
```
</details>

### 5.4 Vérifier la DLQ

Après avoir relancé le test des poison pills :

```bash
docker exec -it kafka kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic dlq-payment \
    --from-beginning
```

---

## Partie 6 : Analytics en Temps Réel avec Kafka Streams (15 min)

### 6.1 Objectif

Modifier `analytics-service/service.py` pour afficher des statistiques en temps réel.

### 6.2 Implémenter le streaming analytics

**Objectif:** Le service analytics doit :
1. Consommer les événements `payment-successful` et `order-created`
2. Maintenir des statistiques en mémoire
3. Exposer ces stats via une API REST

<details>
<summary>Solution</summary>

```python
from flask import Flask, jsonify
import json
import threading
import time
from confluent_kafka import Consumer

app = Flask(__name__)

analytics = {
        'total_payments': 0,
        'total_orders': 0,
        'total_revenue': 0,
        'users': set(),
        'last_updated': None,
        'payments_per_minute': 0,
        'orders_per_minute': 0
}

analytics_lock = threading.Lock()
payment_timestamps = []
order_timestamps = []

consumer_config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "analytics-service-group",
        "auto.offset.reset": "earliest"
}

consumer = Consumer(consumer_config)

def calculate_rate(timestamps, window_seconds=60):
        """Calcule le taux par minute"""
        now = time.time()
        # Garder seulement les timestamps des dernières 60 secondes
        recent = [t for t in timestamps if now - t < window_seconds]
        return len(recent)

def track_payment(message):
        with analytics_lock:
                user_id = message.get('user_id')
                cart = message.get('cart', [])
                
                analytics['total_payments'] += 1
                if user_id:
                        analytics['users'].add(str(user_id))
                
                total = sum(item.get('price', 0) * item.get('quantity', 1) for item in cart if isinstance(item, dict))
                analytics['total_revenue'] += total
                analytics['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
                
                payment_timestamps.append(time.time())
                analytics['payments_per_minute'] = calculate_rate(payment_timestamps)
                
        print(f"[LIVE] Paiement: +{total}EUR | Total: {analytics['total_revenue']}EUR | {analytics['payments_per_minute']} paiements/min")

def track_order(message):
        with analytics_lock:
                analytics['total_orders'] += 1
                analytics['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
                
                order_timestamps.append(time.time())
                analytics['orders_per_minute'] = calculate_rate(order_timestamps)
                
        print(f"[LIVE] Commande #{message.get('order_id')} | Total: {analytics['total_orders']} | {analytics['orders_per_minute']} commandes/min")

def kafka_consumer_loop():
        consumer.subscribe(["payment-successful", "order-created"])
        print("Analytics en écoute sur 'payment-successful' et 'order-created'...")
        
        while True:
                msg = consumer.poll(1.0)
                
                if msg is None:
                        continue
                if msg.error():
                        print(f"Erreur: {msg.error()}")
                        continue
                        
                try:
                        data = json.loads(msg.value().decode('utf-8'))
                        
                        if msg.topic() == "payment-successful":
                                track_payment(data)
                        elif msg.topic() == "order-created":
                                track_order(data)
                                
                except Exception as e:
                        print(f"Erreur analytics: {e}")

@app.route('/analytics', methods=['GET'])
def get_analytics():
        with analytics_lock:
                stats = analytics.copy()
                stats['unique_users'] = len(analytics['users'])
                stats['users'] = list(analytics['users'])[:10]  # Limiter pour l'affichage
        
        return jsonify(stats), 200

@app.route('/analytics/live', methods=['GET'])
def get_live_stats():
        """Endpoint pour stats en temps réel"""
        with analytics_lock:
                return jsonify({
                        'payments_per_minute': analytics['payments_per_minute'],
                        'orders_per_minute': analytics['orders_per_minute'],
                        'total_revenue': analytics['total_revenue'],
                        'last_updated': analytics['last_updated']
                }), 200

if __name__ == '__main__':
        consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
        consumer_thread.start()
        
        print("Service Analytics démarré sur le port 8003")
        app.run(host='0.0.0.0', port=8003, debug=False)
```
</details>

### 6.3 Tester le streaming

1. Lancez le service analytics :
```bash
python analytics-service/service.py
```

2. Lancez la simulation Black Friday dans un autre terminal :
```bash
python scripts/black_friday_simulation.py -n 100 -c 20
```

3. Observez les statistiques en temps réel :
```bash
# Dans un autre terminal
watch -n 1 'curl -s http://localhost:8003/analytics/live | python -m json.tool'
```

---

## Partie 7 : Défis Bonus

### Défi 1 : Réplication pour la haute disponibilité

Modifiez le `docker-compose.yml` pour avoir un cluster de 3 brokers Kafka et configurez la réplication factor à 3.

### Défi 2 : Exactly-once semantics

Configurez les transactions Kafka pour garantir qu'un message n'est traité qu'une seule fois.

### Défi 3 : Schema Registry

Ajoutez un Schema Registry et utilisez Avro pour valider le format des messages.

---

## Ressources

- [Documentation Apache Kafka](https://kafka.apache.org/documentation/)
- [Confluent Kafka Python](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/)
- [Kafka UI](https://github.com/provectus/kafka-ui)

---

## Nettoyage

```bash
# Arrêter les containers
cd kafka
docker compose down

# Supprimer les volumes (optionnel - supprime toutes les données)
docker compose down -v

# Désactiver l'environnement virtuel
deactivate
```


---
