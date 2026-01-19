## 🧪 Exercice 2 : Observer la distribution des messages

### Objectif
Comprendre comment Kafka distribue les messages entre les partitions quand aucune clé n'est spécifiée.

### Étape 1 : Modifier le producer pour afficher la partition

Modifiez la fonction `delivery_report` dans **payment_service.py** :

```python
def delivery_report(err, msg):
    if err:
        print(f"❌ Kafka delivery failed: {err}")
    else:
        print(f"✅ Message envoyé → Topic: {msg.topic()} | Partition: {msg.partition()} | Offset: {msg.offset()}")
```

### Étape 2 : Redémarrer le service

```bash
python payment_service.py
```

### Étape 3 : Envoyer plusieurs paiements

Utilisez Postman pour envoyer **10 paiements différents** avec des `user_id` différents :

```json
{"user_id": "user1", "cart": [{"product": "Laptop", "price": 999, "quantity": 1}]}
{"user_id": "user2", "cart": [{"product": "Mouse", "price": 29, "quantity": 1}]}
{"user_id": "user3", "cart": [{"product": "Keyboard", "price": 79, "quantity": 1}]}
...
```

### Étape 4 : Observer les logs

Dans la console du payment service, vous verrez :

```
✅ Message envoyé → Topic: payment-successful | Partition: 1 | Offset: 0
✅ Message envoyé → Topic: payment-successful | Partition: 0 | Offset: 0
✅ Message envoyé → Topic: payment-successful | Partition: 2 | Offset: 0
✅ Message envoyé → Topic: payment-successful | Partition: 1 | Offset: 1
...
```

### Étape 5 : Visualiser dans Kafka UI

1. Ouvrir **http://localhost:8080**
2. Cliquer sur **Topics** → `payment-successful`
3. Cliquer sur **Messages**
4. Observer la colonne **Partition**

### 💡 Questions de réflexion

1. **Les messages sont-ils répartis uniformément entre les 3 partitions ?**
   
   💬 *Réponse* : Oui, approximativement. Kafka utilise un algorithme de round-robin quand aucune clé n'est fournie.

2. **Comment Kafka décide quelle partition utiliser sans clé ?**
   
   💬 *Réponse* : Kafka utilise un sticky partitioner : il envoie plusieurs messages consécutifs dans la même partition pour optimiser les performances, puis change de partition.

3. **Y a-t-il un ordre global entre les partitions ?**
   
   💬 *Réponse* : Non ! L'ordre est garanti UNIQUEMENT au sein d'une partition, pas entre partitions.

---

## 🧪 Exercice 3 : Partitioning avec clé (Key-based partitioning)

### Objectif
Garantir que tous les messages d'un même utilisateur vont dans la même partition pour préserver l'ordre.

### Concept théorique

```
Sans clé (round-robin) :          Avec clé (user_id) :
user123 → Partition 0              user123 → Partition 1
user123 → Partition 2              user123 → Partition 1
user456 → Partition 1              user123 → Partition 1
user123 → Partition 0              user456 → Partition 0
                                   user456 → Partition 0
❌ Ordre non garanti               ✅ Ordre garanti par user
```

### Étape 1 : Modifier le producer

Dans **payment_service.py**, ajoutez la clé :

```python
@app.route('/payment', methods=['POST'])
def process_payment():
    data = request.get_json()
    cart = data.get('cart')
    user_id = data.get('user_id')
    
    print(f"💳 Traitement du paiement pour l'utilisateur {user_id}")
    
    event = {
        "user_id": user_id,
        "cart": cart,
        "timestamp": time.time()
    }

    # ✅ AJOUT DE LA CLÉ
    producer.produce(
        topic="payment-successful",
        key=user_id.encode('utf-8'),  # ← LA CLÉ DÉTERMINE LA PARTITION
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
```

### Étape 2 : Tester avec le même user_id

Envoyez **5 paiements** avec `user_id: "user123"` :

```bash
# Observez les logs du payment service
```

**Résultat attendu** :
```
✅ Message envoyé → Topic: payment-successful | Partition: 1 | Offset: 0
✅ Message envoyé → Topic: payment-successful | Partition: 1 | Offset: 1
✅ Message envoyé → Topic: payment-successful | Partition: 1 | Offset: 2
✅ Message envoyé → Topic: payment-successful | Partition: 1 | Offset: 3
✅ Message envoyé → Topic: payment-successful | Partition: 1 | Offset: 4
```

👉 Tous les messages de `user123` vont dans la **même partition** (ici Partition 1) !

### Étape 3 : Tester avec un autre user_id

Envoyez **5 paiements** avec `user_id: "user456"` :

**Résultat attendu** :
```
✅ Message envoyé → Topic: payment-successful | Partition: 0 | Offset: 0
✅ Message envoyé → Topic: payment-successful | Partition: 0 | Offset: 1
✅ Message envoyé → Topic: payment-successful | Partition: 0 | Offset: 2
✅ Message envoyé → Topic: payment-successful | Partition: 0 | Offset: 3
✅ Message envoyé → Topic: payment-successful | Partition: 0 | Offset: 4
```

👉 Tous les messages de `user456` vont dans une **autre partition** (ici Partition 0) !

### 💡 Questions de réflexion

1. **Comment Kafka choisit la partition à partir de la clé ?**
   
   💬 *Réponse* : Kafka calcule un **hash** de la clé : `hash(key) % nombre_de_partitions`. Le même user_id donnera toujours le même hash, donc la même partition.

2. **Pourquoi est-ce important pour l'ordre des messages ?**
   
   💬 *Réponse* : Si tous les paiements d'un utilisateur vont dans la même partition, on peut garantir qu'ils seront traités dans l'ordre d'envoi.

3. **Quel est l'inconvénient du key-based partitioning ?**
   
   💬 *Réponse* : Si un user fait beaucoup de transactions, sa partition peut devenir un "hot spot" (surchargée). Il faut bien choisir sa clé de partitioning.

---

## 🧪 Exercice 4 : Scalabilité horizontale avec Consumer Groups

### Objectif
Lancer plusieurs instances du même service pour traiter les messages en parallèle.

### Concept : Consumer Groups

```
1 Consumer Group avec 3 Consumers :

Topic payment-successful (3 partitions)
┌─────────────┐
│ Partition 0 │ → Consumer 1
├─────────────┤
│ Partition 1 │ → Consumer 2
├─────────────┤
│ Partition 2 │ → Consumer 3
└─────────────┘

Chaque partition est assignée à UN SEUL consumer du groupe.
Si un consumer tombe, ses partitions sont réassignées !
```

### Étape 1 : Modifier le order service

Modifiez **order_service.py** pour afficher la partition :

```python
def kafka_consumer_loop():
    consumer.subscribe(["payment-successful"])  # ← Changez pour écouter payment-successful
    print("🎧 Consumer démarré, en écoute sur 'payment-successful'...")
    
    try:
        while True:
            msg = consumer.poll(1.0)
            
            if msg is None:
                continue
            if msg.error():
                print(f"❌ Erreur: {msg.error()}")
                continue
                
            try:
                data = json.loads(msg.value().decode('utf-8'))
                # ✅ AFFICHER LA PARTITION ET LE CONSUMER
                print(f"📨 [Partition {msg.partition()}] [Offset {msg.offset()}] Message reçu pour user {data.get('user_id')}")
                process_payment_event(data)
            except Exception as e:
                print(f"❌ Erreur de traitement: {e}")
    except KeyboardInterrupt:
        print("🛑 Arrêt du consumer...")
    finally:
        consumer.close()
```

### Étape 2 : Lancer 3 instances du order service

Ouvrez **3 terminaux** différents :

```bash
# Terminal 1
python order_service.py

# Terminal 2
python order_service.py

# Terminal 3
python order_service.py
```

### Étape 3 : Observer l'assignation des partitions

Chaque instance affichera quelque chose comme :

```
Instance 1 :
🎧 Consumer démarré, en écoute sur 'payment-successful'...
📊 Partition assignée : 0

Instance 2 :
🎧 Consumer démarré, en écoute sur 'payment-successful'...
📊 Partition assignée : 1

Instance 3 :
🎧 Consumer démarré, en écoute sur 'payment-successful'...
📊 Partition assignée : 2
```

### Étape 4 : Envoyer des messages

Envoyez rapidement **10 paiements** via Postman (différents user_id).

### Étape 5 : Observer la distribution

Vous verrez que **chaque instance traite uniquement les messages de SA partition** :

```
Instance 1 (Partition 0) :
📨 [Partition 0] [Offset 0] Message reçu pour user user2
📨 [Partition 0] [Offset 1] Message reçu pour user user5

Instance 2 (Partition 1) :
📨 [Partition 1] [Offset 0] Message reçu pour user user1
📨 [Partition 1] [Offset 1] Message reçu pour user user3

Instance 3 (Partition 2) :
📨 [Partition 2] [Offset 0] Message reçu pour user user4
📨 [Partition 2] [Offset 1] Message reçu pour user user6
```

### 💡 Questions de réflexion

1. **Que se passe-t-il si on a 3 partitions et 1 seul consumer ?**
   
   💬 *Réponse* : Le consumer unique consomme TOUTES les partitions. Aucun parallélisme.

2. **Que se passe-t-il si on a 3 partitions et 5 consumers ?**
   
   💬 *Réponse* : Seulement 3 consumers seront actifs (1 par partition). Les 2 autres seront en "standby" et ne recevront rien.

3. **Que se passe-t-il si on a 3 partitions et 3 consumers, puis qu'on arrête 1 consumer ?**
   
   💬 *Réponse* : Les 2 consumers restants se partagent les 3 partitions (l'un en aura 2, l'autre 1).

4. **Quel est le nombre optimal de consumers ?**
   
   💬 *Réponse* : Idéalement, **1 consumer par partition** pour maximiser le parallélisme sans gaspillage.

---

## 🧪 Exercice 5 : Ordre des messages

### Objectif
Comprendre que l'ordre est garanti par partition, mais pas globalement.

### Étape 1 : Créer un script de test

Créez **test_ordering.py** :

```python
import requests
import json
import time

def test_ordering_with_key():
    """Test avec clé : ordre garanti"""
    print("=== TEST AVEC CLÉ (même user) ===")
    
    for i in range(1, 6):
        payment_data = {
            "user_id": "user123",  # Même user = même partition
            "cart": [
                {"product": f"Product-{i}", "price": 10.0 * i, "quantity": 1}
            ]
        }
        
        print(f"📤 Envoi du paiement #{i} pour user123")
        response = requests.post("http://localhost:8000/payment", json=payment_data)
        time.sleep(0.2)
    
    print("\n" + "="*50 + "\n")

def test_ordering_without_key():
    """Test sans clé : ordre non garanti"""
    print("=== TEST SANS CLÉ (users différents) ===")
    
    for i in range(1, 6):
        payment_data = {
            "user_id": f"user{i}",  # Users différents = partitions différentes
            "cart": [
                {"product": f"Product-{i}", "price": 10.0 * i, "quantity": 1}
            ]
        }
        
        print(f"📤 Envoi du paiement #{i} pour user{i}")
        response = requests.post("http://localhost:8000/payment", json=payment_data)
        time.sleep(0.2)
    
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    print("🧪 Test de l'ordre des messages\n")
    
    # Test 1 : Avec la même clé
    test_ordering_with_key()
    time.sleep(2)
    
    # Test 2 : Avec des clés différentes
    test_ordering_without_key()
    
    print("✅ Tests terminés ! Observez les logs des services.")
```

### Étape 2 : Exécuter le script

```bash
python test_ordering.py
```

### Étape 3 : Observer les résultats

**Avec clé (même user)** :
```
Payment Service :
✅ Message envoyé → Partition: 1 | Offset: 0
✅ Message envoyé → Partition: 1 | Offset: 1
✅ Message envoyé → Partition: 1 | Offset: 2
✅ Message envoyé → Partition: 1 | Offset: 3
✅ Message envoyé → Partition: 1 | Offset: 4

Order Service :
📨 [Partition 1] [Offset 0] Product-1
📨 [Partition 1] [Offset 1] Product-2
📨 [Partition 1] [Offset 2] Product-3
📨 [Partition 1] [Offset 3] Product-4
📨 [Partition 1] [Offset 4] Product-5
```
👉 **Ordre respecté** car même partition !

**Sans clé (users différents)** :
```
Payment Service :
✅ Message envoyé → Partition: 0 | Offset: 0
✅ Message envoyé → Partition: 2 | Offset: 0
✅ Message envoyé → Partition: 1 | Offset: 0
✅ Message envoyé → Partition: 0 | Offset: 1
✅ Message envoyé → Partition: 2 | Offset: 1

Order Service :
📨 [Partition 2] [Offset 0] Product-2
📨 [Partition 0] [Offset 0] Product-1
📨 [Partition 1] [Offset 0] Product-3
📨 [Partition 2] [Offset 1] Product-5
📨 [Partition 0] [Offset 1] Product-4
```
👉 **Ordre NON respecté** car partitions différentes !

### 💡 Questions de réflexion

1. **Pourquoi l'ordre est-il important pour certaines applications ?**
   
   💬 *Réponse* : Exemples : transactions bancaires (débit avant crédit), historique de navigation, logs d'audit.

2. **Quand peut-on accepter le désordre ?**
   
   💬 *Réponse* : Quand les événements sont indépendants (ex: différents utilisateurs, métriques analytics).

3. **Comment garantir l'ordre global dans Kafka ?**
   
   💬 *Réponse* : Utiliser un seul topic avec UNE SEULE partition. Mais attention, perte de parallélisme !

---