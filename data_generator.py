
import random
import uuid
from datetime import datetime, timezone

def generate_event():
    """
    Generates a random event conforming to the PurchaseRequestEventV1 schema.
    """
    now = datetime.now(timezone.utc).isoformat()

    return {
        "Composite": "PurchaseRequestEventV1",
        "Details": {
            "EventAt": now,
            "TraceId": uuid.uuid4().hex,
            "SpanId": uuid.uuid4().hex[:16],
            "ParentSpanId": uuid.uuid4().hex[:16],
            "Component": random.choice(["PurchaseService", "RefundService", "CryptoService", "KeyManagerService", "AcquirerService"]),
            "Method": "ProcessTransaction",
            "Info": "A sample transaction event.",
            "Activity": random.choice(["Started", "Stopped", "Created", "Sent", "Received", "Warning", "Exception"]),
            "SentAt": now,
            "OrganizationId": str(uuid.uuid4()),
            "IdempotencyKey": str(uuid.uuid4()),
            "DataClassification": random.choice(["Green", "Amber", "Red", "Blue"]),
            "Category": random.choice(["Critical", "Warning", "Performance", "Error", "Notice", "Informational", "Debug"])
        },
        "State": {
            "MerchantId": str(uuid.uuid4()),
            "InstanceId": str(uuid.uuid4()),
            "TransactionId": str(uuid.uuid4()),
            "CorrelationId": str(uuid.uuid4()),
            "RequestTimestampUtc": now,
            "CustomerReference": "CUST" + "".join(random.choices("0123456789", k=8)),
            "RequestMeta": None,
            "PanStart": "".join(random.choices("0123456789", k=6)),
            "PanStartEight": "".join(random.choices("0123456789", k=8)),
            "PanEnd": "".join(random.choices("0123456789", k=4)),
            "PanSequenceNumber": "01",
            "CardApplicationId": "A0000000041010",
            "EntryMode": random.choice(["CONTACTLESS", "CHIP", "SWIPE"]),
            "Scheme": "VISA",
            "SchemeId": "1",
            "CardApplicationLabel": "VISA DEBIT",
            "CardApplicationPreferredName": None,
            "CardholderVerificationMethod": "PIN",
            "CardholderVerificationMethodResults": None,
            "Amount": random.randint(100, 100000),
            "AmountFormatted": f"{random.uniform(1.00, 1000.00):.2f}",
            "Currency": "USD",
            "CurrencyCode": "840",
            "RequestProductFeatures": None,
            "ApplicationCryptogram": None,
            "Platform": "POS",
            "TransactionType": "PURCHASE"
        }
    }
