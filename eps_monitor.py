import argparse
import time
from kafka import KafkaConsumer
from confluent_kafka.avro import AvroConsumer
from confluent_kafka import KafkaError

def main():
    parser = argparse.ArgumentParser(description="Kafka EPS Monitor")
    parser.add_argument("--topic", required=True, help="Kafka topic to monitor")
    parser.add_argument("--broker", required=True, help="Kafka broker address")
    parser.add_argument("--interval", type=int, default=5, help="Interval in seconds to calculate and report EPS")
    parser.add_argument("--avro", action='store_true', help="Use Avro consumer instead of standard consumer")
    parser.add_argument("--schema-registry", help="Schema Registry URL (required for --avro)")
    args = parser.parse_args()

    if args.avro and not args.schema_registry:
        parser.error("--schema-registry is required when using --avro")

    print(f"Connecting to Kafka broker at {args.broker}...")
    
    if args.avro:
        consumer_config = {
            'bootstrap.servers': args.broker,
            'group.id': 'eps-monitor-group',
            'schema.registry.url': args.schema_registry,
            'auto.offset.reset': 'latest'
        }
        try:
            consumer = AvroConsumer(consumer_config)
            consumer.subscribe([args.topic])
            print("Using Avro Consumer.")
        except Exception as e:
            print(f"Failed to create AvroConsumer: {e}")
            return
    else:
        try:
            consumer = KafkaConsumer(
                args.topic,
                bootstrap_servers=[args.broker],
                auto_offset_reset='latest',
                consumer_timeout_ms=1000
            )
            print("Using Standard Consumer.")
        except Exception as e:
            print(f"Failed to create KafkaConsumer: {e}")
            return

    print(f"Successfully connected. Monitoring topic '{args.topic}'...")
    print(f"Calculating EPS every {args.interval} seconds. Press Ctrl+C to stop.")

    try:
        while True:
            start_time = time.time()
            message_count = 0
            
            while time.time() - start_time < args.interval:
                if args.avro:
                    # AvroConsumer's poll is different
                    msg = consumer.poll(1.0) # Timeout of 1 second
                    if msg is None:
                        continue
                    if msg.error():
                        if msg.error().code() != KafkaError._PARTITION_EOF:
                            print(f"AvroConsumer error: {msg.error()}")
                    else:
                        message_count += 1
                else:
                    # Standard KafkaConsumer poll
                    messages = consumer.poll(timeout_ms=500)
                    if messages:
                        for tp, records in messages.items():
                            message_count += len(records)

            end_time = time.time()
            elapsed_time = end_time - start_time

            if elapsed_time > 0:
                eps = message_count / elapsed_time
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Current EPS: {eps:.2f}")
            else:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] No messages received in the last interval.")

    except KeyboardInterrupt:
        print("\nStopping monitor.")
    finally:
        if 'consumer' in locals():
            consumer.close()
            print("Consumer closed.")

if __name__ == "__main__":
    main()