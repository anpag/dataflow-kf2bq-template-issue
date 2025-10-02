from faker import Faker

from faker import Faker
import random
import uuid

def generate_event(add_hotkey=False):
    fake = Faker()

    # Generate amount first to ensure consistency between Amount and AmountFormatted
    amount_long = fake.pyint(min_value=100, max_value=100000)
    amount_formatted = f"{amount_long / 100:.2f}"

    event_data = {
        "Composite": fake.bs(),
        "Details": {
            "EventAt": fake.iso8601(),
            "TraceId": fake.hexify(text='^' * 32),
            "SpanId": fake.hexify(text='^' * 16),
            "ParentSpanId": fake.hexify(text='^' * 16),
            "Component": random.choice(["PurchaseService", "RefundService", "CryptoService", "KeyManagerService", "AcquirerService"]),
            "Method": fake.word(),
            "Info": random.choice([None, fake.sentence()]),
            "Activity": random.choice(["Started", "Stopped", "Created", "Sent", "Received", "Warning", "Exception"]),
            "SentAt": fake.iso8601(),
            "OrganizationId": random.choice([None, str(uuid.uuid4())]),
            "IdempotencyKey": str(uuid.uuid4()),
            "DataClassification": random.choice(["Green", "Amber", "Red", "Blue"]),
            "Category": random.choice(["Critical", "Warning", "Performance", "Error", "Notice", "Informational", "Debug"])
        },
        "State": {
            "MerchantId": str(uuid.uuid4()),
            "InstanceId": str(uuid.uuid4()),
            "TransactionId": str(uuid.uuid4()),
            "CorrelationId": str(uuid.uuid4()),
            "RequestTimestampUtc": fake.iso8601(),
            "CustomerReference": fake.pystr(min_chars=10, max_chars=20),
            "RequestMeta": random.choice([None, fake.json()]),
            "PanStart": fake.numerify(text='######'),
            "PanStartEight": random.choice([None, fake.numerify(text='########')]),
            "PanEnd": fake.numerify(text='####'),
            "PanSequenceNumber": random.choice([None, fake.numerify(text='##')]),
            "CardApplicationId": fake.hexify(text='^' * 16),
            "EntryMode": fake.word(),
            "Scheme": fake.credit_card_provider(),
            "SchemeId": fake.numerify(text='##'),
            "CardApplicationLabel": random.choice([None, fake.word()]),
            "CardApplicationPreferredName": random.choice([None, fake.word()]),
            "CardholderVerificationMethod": fake.word(),
            "CardholderVerificationMethodResults": random.choice([None, fake.hexify(text='^' * 8)]),
            "Amount": amount_long,
            "AmountFormatted": amount_formatted,
            "Currency": fake.currency_code(),
            "CurrencyCode": fake.numerify(text='###'),
            "RequestProductFeatures": random.choice([None, fake.json()]),
            "ApplicationCryptogram": random.choice([None, fake.hexify(text='^' * 16)]),
            "Platform": fake.word(),
            "TransactionType": fake.word()
        }
    }

    if add_hotkey:
        event_data["hotkeyId"] = random.randint(1, 50)

    return event_data