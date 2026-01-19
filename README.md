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
| `email-sent` | Événements d'envoi d'emails
| `dlq-payment` | Dead Letter Queue pour les erreurs |

<details>
<summary>Solution</summary>

```bash
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 \
    --create --topic order-created --partitions 1 --replication-factor 1

docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 \
    --create --topic email-sent --partitions 1 --replication-factor 1

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

**Objectif:** Modifier `email-service/service.py` pour consommer les messages du topic `order-created` et produire des messages sur le topic `email-sent`.

**TODO:**

1. Importer Consumer et Producer Kafka
2. Créer la configuration du consumer pour le topic `order-created`
3. Créer une fonction `send_confirmation_email` pour envoyer les emails
4. Produire un message sur le topic `email-sent` après envoi
5. Implémenter la boucle de consommation

<details>
<summary>Indices</summary>

```python
from confluent_kafka import Consumer, Producer

consumer_config = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "email-service-group",
    "auto.offset.reset": "earliest"
}

producer_config = {
    "bootstrap.servers": "localhost:9092"
}

consumer = Consumer(consumer_config)
producer = Producer(producer_config)
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

emails_sent = []

consumer_config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "email-service-group",
        "auto.offset.reset": "earliest"
}

producer_config = {
    "bootstrap.servers": "localhost:9092"
}

consumer = Consumer(consumer_config)
producer = Producer(producer_config)

def delivery_report(err, msg):
    if err:
        print(f"❌ Kafka delivery failed: {err}")
    else:
        print(f"✅ Message sent to {msg.topic()} [partition {msg.partition()}]")


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

        # Produire un message dans le topic 'email-sent'
        email_event = {
                'user_id': user_id,
                'order_id': order_id,
                'email_to': email['to'],
                'subject': email['subject'],
                'status': 'sent'
        }
        
        producer.produce(
                topic="email-sent",
                value=json.dumps(email_event).encode("utf-8"),
                callback=delivery_report
        )
        producer.flush()

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

**Lancez le service :**
```bash
python email-service/service.py
```

**Vérification:** Allez sur Kafka UI et vérifiez :
1. Le service écoute le topic `order-created`
2. Il produit des messages sur le topic `email-sent`
3. Les emails sont stockés dans la liste `emails_sent`

**Testez avec curl :**
```bash
# Vérifier les emails envoyés
curl http://localhost:8002/emails
```

### 2.4 Le Service Analytics (Multi-Consumer)

**Objectif:** Modifier `analytics-service/service.py` pour consommer les messages provenant de PLUSIEURS topics (`payment-successful`, `order-created`, `email-sent`) et maintenir des statistiques en temps réel.

**TODO:**

1. Importer Consumer Kafka
2. Créer la configuration du consumer
3. S'abonner à plusieurs topics
4. Implémenter des fonctions de tracking pour chaque événement
5. Mantenir des statistiques en mémoire (total paiements, commandes, emails, revenus, utilisateurs uniques)
6. Exposer une API `/analytics` pour consulter les stats

<details>
<summary>Indices</summary>

```python
from confluent_kafka import Consumer

consumer_config = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "analytics-service-group",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": True
}

consumer = Consumer(consumer_config)
# S'abonner à plusieurs topics
consumer.subscribe(["payment-successful", "order-created", "email-sent"])
```
</details>

<details>
<summary>Solution complète</summary>

```python
from flask import Flask, jsonify
import json
import threading
from confluent_kafka import Consumer

app = Flask(__name__)

# Statistiques en mémoire
analytics = {
    'total_payments': 0,
    'total_orders': 0,
    'total_emails': 0,
    'total_revenue': 0,
    'users': set()
}

# Configuration du consumer
consumer_config = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "analytics-service-group",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": True
}

consumer = Consumer(consumer_config)

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

def track_email(message):
    """
    Enregistre les statistiques d'email
    """
    order_id = message.get('order_id')
    email_to = message.get('email_to')
    
    analytics['total_emails'] += 1
    
    print(f"📊 Email enregistré: {email_to} pour commande #{order_id}")


@app.route('/analytics', methods=['GET'])
def get_analytics():
    stats = analytics.copy()
    stats['unique_users'] = len(analytics['users'])
    stats['users'] = list(analytics['users'])
    
    return jsonify(stats), 200


def kafka_consumer_loop():
    """
    Thread qui consomme les messages de plusieurs topics
    """
    # S'abonner à plusieurs topics
    consumer.subscribe(["payment-successful", "order-created", "email-sent"])
    print("🎧 Consumer démarré, écoute sur 3 topics:")
    print("   - payment-successful")
    print("   - order-created")
    print("   - email-sent")
    
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                print(f"❌ Consumer error: {msg.error()}")
                continue
            
            # Décoder le message
            try:
                message_value = json.loads(msg.value().decode('utf-8'))
                topic = msg.topic()
                
                print(f"📨 Message reçu de '{topic}'")
                
                # Router vers la bonne fonction selon le topic
                if topic == "payment-successful":
                    track_payment(message_value)
                elif topic == "order-created":
                    track_order(message_value)
                elif topic == "email-sent":
                    track_email(message_value)
                else:
                    print(f"⚠️ Topic inconnu: {topic}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Erreur de décodage JSON: {e}")
            except Exception as e:
                print(f"❌ Erreur lors du traitement: {e}")
                
    except KeyboardInterrupt:
        print("🛑 Arrêt du consumer...")
    finally:
        consumer.close()

if __name__ == '__main__':
    # Démarrer le consumer Kafka dans un thread séparé
    consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
    consumer_thread.start()

    print("🚀 Service d'analytics démarré sur le port 8003")
    print("⏳ En attente d'événements...")
    app.run(host='0.0.0.0', port=8003, debug=False)
```
</details>

**Lancez le service :**
```bash
python analytics-service/service.py
```


### 2.5 Test de l'intégration

Lancez tous les services dans des terminaux séparés :

```bash
# Terminal 1
python payment-service/service.py

# Terminal 2
python order-service/service.py

# Terminal 3
python email-service/service.py

# Terminal 4
python analytics-service/service.py
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
4. Les statistiques de chaque service qui s'affichent (Terminal 4)

---

## Partie 3 : Simulation Black Friday - Observer le problème

Le but de cette partie est de **voir le problème** : avec une seule partition et un seul consumer, le système ne peut pas absorber un pic de charge.

### 3.1 Comprendre le LAG

Le **LAG** est la différence entre :
- Le nombre de messages produits dans Kafka
- Le nombre de messages consommés par votre consumer

```
Messages produits:    [============================] 5000
Messages consommés:   [========]                     1200
                      ↑
                      LAG = 3800 messages en retard!
```

Un LAG élevé signifie que votre consumer n'arrive pas à suivre le rythme de production.

### 3.2 Ajouter un délai de traitement au consumer

Pour simuler un traitement réaliste (accès base de données, appels API, etc.), modifiez votre `order-service/service.py` pour ajouter un délai dans `process_payment_event`:

```python
import time

def process_payment_event(message):
    user_id = message.get('user_id')
    cart = message.get('cart')
    
    # Simulation d'un traitement lent (accès DB, validation, etc.)
    time.sleep(0.1)  # 100ms par message = max 10 messages/seconde
    
    order = {
        'order_id': len(orders) + 1,
        'user_id': user_id,
        'items': cart,
        'status': 'confirmed'
    }
    # ... reste du code
```

### 3.3 Lancer la simulation Black Friday

**Terminal 1 - Lancez votre order-service:**
```bash
python order-service/service.py
```

**Terminal 2 - Injectez 1000 messages dans Kafka:**
```bash
python scripts/kafka_flood.py -n 1000
```

Vous verrez que les 1000 messages sont envoyés en quelques secondes.

### 3.4 Observer le LAG

**Terminal 3 - Surveillez le lag en temps réel:**
```bash
python scripts/check_consumer_lag.py --monitor
```

Vous devriez voir quelque chose comme :
```
⏰ 14:32:15
   order-service-group → payment-successful: 🔥 Lag = 847
⏰ 14:32:17
   order-service-group → payment-successful: 🔥 Lag = 823
⏰ 14:32:19
   order-service-group → payment-successful: 🔥 Lag = 801
```

**Le consumer traite ~10 messages/seconde, mais on en a injecté 1000 en 2 secondes !**

### 3.5 Mode intense 🔥

Essayez avec plus de messages :

```bash
python scripts/kafka_flood.py --intense  # 5000 messages
```

Le LAG explose ! Votre unique consumer met plusieurs minutes à rattraper son retard.

**Problème identifié:** Avec une seule partition et un seul consumer, le système ne tient pas la charge !

---

## Partie 4 : Optimisation avec les Partitions et Consumer Groups

### 4.1 Comprendre les partitions

Les partitions permettent de paralléliser le traitement des messages. **Chaque partition ne peut être lue que par UN seul consumer du même groupe.**

```
                    Topic: payment-successful (3 partitions)
        ┌─────────────────┬─────────────────┬─────────────────┐
        │   Partition 0   │   Partition 1   │   Partition 2   │
        │   (messages     │   (messages     │   (messages     │
        │    1, 4, 7...)  │    2, 5, 8...)  │    3, 6, 9...)  │
        └────────┬────────┴────────┬────────┴────────┬────────┘
                 │                 │                 │
                 ▼                 ▼                 ▼
            Consumer 1        Consumer 2        Consumer 3
            (10 msg/s)        (10 msg/s)        (10 msg/s)
                              
                    = 30 messages/seconde au total!
```

**Règle importante:** Nombre de consumers ≤ Nombre de partitions

### 4.2 Arrêter les services et recréer les topics

```bash
# Arrêtez tous vos services (Ctrl+C)

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

### 4.3 Lancer 3 instances du consumer

Ouvrez **3 terminaux** et lancez une instance du service dans chacun :

**Terminal 1:**
```bash
python order-service/service.py
```

**Terminal 2:**
```bash
PORT=8011 python order-service/service.py
```

**Terminal 3:**
```bash
PORT=8012 python order-service/service.py
```

> 💡 Les 3 instances partagent le même `group.id`, donc Kafka va automatiquement distribuer les partitions entre elles !

### 4.4 Vérifier la distribution dans Kafka UI

1. Allez sur Kafka UI : http://localhost:8080
2. Cliquez sur **"Consumers"** dans le menu
3. Cliquez sur **"order-service-group"**
4. Observez : chaque consumer a sa propre partition assignée !

### 4.5 Relancer la simulation et comparer

**Terminal 4 - Injectez à nouveau 1000 messages:**
```bash
python scripts/kafka_flood.py -n 1000
```

**Terminal 5 - Surveillez le lag:**
```bash
python scripts/check_consumer_lag.py --monitor
```

### 4.6 Comparer les résultats

| Configuration | Débit de traitement | Temps pour 1000 messages |
|--------------|---------------------|--------------------------|
| 1 partition, 1 consumer | ~10 msg/s | ~100 secondes |
| 3 partitions, 3 consumers | ~30 msg/s | ~33 secondes |

**Le lag descend 3x plus vite !**

### 4.7 Test extrême

Avec 3 consumers en parallèle :
```bash
python scripts/kafka_flood.py --intense  # 5000 messages
```

Le système gère maintenant beaucoup mieux la charge !

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
