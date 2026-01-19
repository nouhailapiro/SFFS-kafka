etapes tp:

1. créer environnement virtuel:
python -m venv venv

Activez le:
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows

installer les dépendences : pip install -r requirements.txt

créer et lancer les conteneurs Kafka et kafka-ui : docker compose up -d

step 1 : Kafka CLI 
- créer le premier topic payment-successful en utilisant la commande : docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --create --topic payment-successful --partitions 1 --replication-factor 1 
On doit voir en output "Created topic payment-successful"

on peut vérifier sur le Kafka ui que le topic a bien été crée