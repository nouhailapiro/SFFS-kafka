#!/usr/bin/env python3
"""
📊 Vérification du lag des consumer groups
Ce script affiche le lag (retard) de traitement des consumers Kafka.
"""

from confluent_kafka.admin import AdminClient, ConsumerGroupTopicPartitions, TopicPartition
from confluent_kafka import Consumer
import time
import argparse

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

def get_consumer_lag(group_id, topic):
    """
    Calcule le lag d'un consumer group pour un topic donné.
    
    Le LAG = (dernier offset du topic) - (offset actuel du consumer)
    
    Un lag élevé signifie que le consumer n'arrive pas à suivre le rythme de production.
    """
    admin_client = AdminClient({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})
    
    # Créer un consumer temporaire pour obtenir les high watermarks
    temp_consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": f"lag-checker-{int(time.time())}",
        "auto.offset.reset": "earliest"
    })
    
    try:
        # Obtenir les métadonnées du topic
        metadata = admin_client.list_topics(topic=topic, timeout=10)
        
        if topic not in metadata.topics:
            print(f"❌ Topic '{topic}' non trouvé!")
            return None
        
        topic_metadata = metadata.topics[topic]
        partitions = list(topic_metadata.partitions.keys())
        
        # Obtenir les high watermarks (derniers offsets) pour chaque partition
        high_watermarks = {}
        topic_partitions = [TopicPartition(topic, p) for p in partitions]
        temp_consumer.assign(topic_partitions)
        
        for tp in topic_partitions:
            low, high = temp_consumer.get_watermark_offsets(tp, timeout=10)
            high_watermarks[tp.partition] = high
        
        # Obtenir les offsets commités du consumer group
        committed_offsets = {}
        
        try:
            # Créer un consumer avec le group.id cible pour lire les offsets commités
            group_consumer = Consumer({
                "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
                "group.id": group_id,
                "auto.offset.reset": "earliest"
            })
            group_consumer.assign(topic_partitions)
            
            committed = group_consumer.committed(topic_partitions, timeout=10)
            for tp in committed:
                if tp.offset >= 0:
                    committed_offsets[tp.partition] = tp.offset
                else:
                    committed_offsets[tp.partition] = 0
            
            group_consumer.close()
        except Exception as e:
            # Si le groupe n'existe pas encore, offset = 0
            for p in partitions:
                committed_offsets[p] = 0
        
        # Calculer le lag
        total_lag = 0
        partition_lags = {}
        
        for p in partitions:
            high = high_watermarks.get(p, 0)
            committed = committed_offsets.get(p, 0)
            lag = high - committed
            partition_lags[p] = {
                "high_watermark": high,
                "committed_offset": committed,
                "lag": lag
            }
            total_lag += lag
        
        return {
            "group_id": group_id,
            "topic": topic,
            "total_lag": total_lag,
            "partitions": partition_lags
        }
        
    finally:
        temp_consumer.close()

def display_lag(lag_info):
    """Affiche les informations de lag de manière lisible"""
    if lag_info is None:
        return
    
    print()
    print(f"📊 Consumer Group: {lag_info['group_id']}")
    print(f"   Topic: {lag_info['topic']}")
    print("-" * 50)
    
    for partition, info in lag_info['partitions'].items():
        lag = info['lag']
        status = "✅" if lag < 100 else "⚠️ " if lag < 1000 else "🔥"
        print(f"   Partition {partition}: {status} Lag = {lag:,}")
        print(f"      High Watermark: {info['high_watermark']:,}")
        print(f"      Committed:      {info['committed_offset']:,}")
    
    print("-" * 50)
    total = lag_info['total_lag']
    if total == 0:
        print(f"   TOTAL LAG: ✅ {total:,} (parfait!)")
    elif total < 100:
        print(f"   TOTAL LAG: ✅ {total:,} (acceptable)")
    elif total < 1000:
        print(f"   TOTAL LAG: ⚠️  {total:,} (attention)")
    else:
        print(f"   TOTAL LAG: 🔥 {total:,} (CRITIQUE!)")
        print()
        print("   💡 Le consumer n'arrive pas à suivre!")
        print("   → Ajoutez des partitions et des consumers")

def monitor_lag(groups_and_topics, interval=2, duration=30):
    """
    Surveille le lag en continu pendant une durée donnée
    """
    print("=" * 60)
    print("📊 SURVEILLANCE DU LAG EN TEMPS RÉEL")
    print("=" * 60)
    print(f"Durée: {duration}s | Intervalle: {interval}s")
    print("Appuyez sur Ctrl+C pour arrêter")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        while time.time() - start_time < duration:
            print(f"\n⏰ {time.strftime('%H:%M:%S')}")
            
            for group_id, topic in groups_and_topics:
                lag_info = get_consumer_lag(group_id, topic)
                if lag_info:
                    total = lag_info['total_lag']
                    status = "✅" if total < 100 else "⚠️ " if total < 1000 else "🔥"
                    print(f"   {group_id} → {topic}: {status} Lag = {total:,}")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Surveillance arrêtée")

def main():
    parser = argparse.ArgumentParser(description="Vérification du lag des consumers Kafka")
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Mode surveillance continue"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Durée de surveillance en secondes (défaut: 60)"
    )
    
    args = parser.parse_args()
    
    # Consumer groups à surveiller
    groups_and_topics = [
        ("order-service-group", "payment-successful"),
        ("email-service-group", "order-created"),
        ("analytics-service-group", "payment-successful"),
    ]
    
    if args.monitor:
        monitor_lag(groups_and_topics, interval=2, duration=args.duration)
    else:
        print("=" * 60)
        print("📊 VÉRIFICATION DU LAG DES CONSUMERS")
        print("=" * 60)
        
        for group_id, topic in groups_and_topics:
            lag_info = get_consumer_lag(group_id, topic)
            display_lag(lag_info)
        
        print()
        print("=" * 60)
        print("💡 Pour surveiller en continu: python scripts/check_consumer_lag.py --monitor")
        print("=" * 60)

if __name__ == "__main__":
    main()
