import os
import time
import json
import argparse
import requests
import google.generativeai as genai
from confluent_kafka import avro
from confluent_kafka.avro import AvroProducer
from dotenv import load_dotenv
from faker import Faker
import sys
import importlib.util
import cProfile
import pstats

# Load environment variables from .env file
load_dotenv()

GENERATED_FUNCTIONS_DIR = "generated_functions"

def get_schema_from_registry(schema_registry_url, subject):
    """Fetches the latest schema for a subject from the Schema Registry."""
    url = f"{schema_registry_url}/subjects/{subject}/versions/latest"
    print(f"Fetching schema from {url}...")
    response = requests.get(url)
    response.raise_for_status()
    return response.json()["schema"]

def generate_data_function_with_gemini(schema):
    """Generates a Python function using Gemini to produce random data for a given Avro schema."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')

    prompt = f"""
    You are an expert Python code generator. Your task is to create a Python function named 'generate_event' that uses the Faker library to generate random data conforming to the provided Avro schema.
    **Instructions:**
    1.  The function must be named `generate_event`.
    2.  It must take no arguments.
    3.  It must return a dictionary that strictly matches the structure and data types defined in the Avro schema.
    4.  Your response MUST be only the raw Python code for the function. Do not include any markdown formatting (like ```python), explanations, or any text outside of the function definition.
    **Avro Schema:**
    {schema}
    """
    print("Generating data creation function from schema...")
    response = model.generate_content(prompt)
    full_code = "from faker import Faker\n\n" + response.text
    return full_code

def verify_code_with_gemini(function_code, schema_str):
    """Verifies if the generated Python code conforms to the Avro schema using Gemini."""
    # This function remains the same as before
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')
    prompt = f"""
    You are an expert Avro schema and Python code validator...
    **Avro Schema:**
    ```json
    {schema_str}
    ```
    **Python Function:**
    ```python
    {function_code}
    ```
    Does the Python function generate data that conforms to the Avro schema? Your answer:
    """
    print("Verifying generated code against schema...")
    response = model.generate_content(prompt)
    return response.text.strip().lower()

def production_loop(producer, topic, eps, generate_event_func, add_hotkey=False):
    """The main message production loop."""
    print(f"Streaming events to Kafka topic '{topic}' with a target of {eps} events/sec.")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            for _ in range(eps):
                event = generate_event_func(add_hotkey=add_hotkey)
                producer.produce(topic=topic, value=event)
            producer.poll(0)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping producer.")

def main():
    parser = argparse.ArgumentParser(description="Dynamic Avro Kafka Producer")
    parser.add_argument("--topic", required=True, help="Kafka topic")
    parser.add_argument("--broker", required=True, help="Kafka broker address")
    parser.add_argument("--schema-registry", required=True, help="Schema Registry URL")
    parser.add_argument("--eps", type=int, default=10, help="Target events per second")
    parser.add_argument("--profile", action='store_true', help="Run in profiling mode for 10 seconds to identify bottlenecks.")
    parser.add_argument("--add-hotkey", action='store_true', help="Add a random 'hotkeyId' field to each message to mitigate BigQuery hotkeying.")
    args = parser.parse_args()

    if not os.path.exists(GENERATED_FUNCTIONS_DIR):
        os.makedirs(GENERATED_FUNCTIONS_DIR)

    function_filename = os.path.join(GENERATED_FUNCTIONS_DIR, f"{args.topic}_datagen.py")

    if os.path.exists(function_filename):
        print(f"Loading existing data generation function from {function_filename}...")
        spec = importlib.util.spec_from_file_location("datagen", function_filename)
        datagen_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(datagen_module)
        generate_event = datagen_module.generate_event
    else:
        print("No existing function found. Generating a new one...")
        subject = f"{args.topic}-value"
        schema_str = get_schema_from_registry(args.schema_registry, subject)
        function_code = generate_data_function_with_gemini(schema_str)
        verification_result = verify_code_with_gemini(function_code, schema_str)
        if verification_result != "yes":
            print(f"Verification failed. Gemini response: '{verification_result}'. Exiting.")
            sys.exit(1)
        print("Verification successful.")
        with open(function_filename, "w") as f:
            f.write(function_code)
        print(f"Saved new data generation function to {function_filename}.")
        exec_namespace = {}
        exec(function_code, exec_namespace)
        generate_event = exec_namespace['generate_event']

    subject = f"{args.topic}-value"
    schema_str = get_schema_from_registry(args.schema_registry, subject)
    value_schema = avro.loads(schema_str)

    producer_config = {
        "bootstrap.servers": args.broker,
        "schema.registry.url": args.schema_registry,
        "linger.ms": 100,
        "batch.size": 1024 * 1024,
        "compression.codec": "snappy",
        "acks": "1"
    }
    producer = AvroProducer(producer_config, default_value_schema=value_schema)

    if args.profile:
        print("--- PROFILING MODE ---")
        print("Running for 10 seconds to gather performance data...")
        
        # Create a profiler object
        profiler = cProfile.Profile()
        
        # Define a short-lived production loop for profiling
        def profile_loop():
            start_time = time.time()
            while time.time() - start_time < 10:
                for _ in range(args.eps):
                    event = generate_event()
                    producer.produce(topic=args.topic, value=event)
                producer.poll(0)
                time.sleep(1)

        # Run the profiler
        profiler.enable()
        profile_loop()
        profiler.disable()

        # Print the stats
        print("\n--- PROFILING RESULTS ---")
        stats = pstats.Stats(profiler).sort_stats('cumulative')
        stats.print_stats(20) # Print the top 20 cumulative time offenders
        print("--- END OF REPORT ---")

    else:
        production_loop(producer, args.topic, args.eps, generate_event, args.add_hotkey)

    print("Flushing final messages...")
    producer.flush()
    print("Producer closed.")

if __name__ == "__main__":
    main()