import sys
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-a9da68b5f222"
COLLECTION_NAME = "subscriptions"

SEED_ITEMS = [
    {
        "id": "sub_001",
        "name": "Netflix Premium 4K",
        "category": "subscription",
        "cost": 22.99,
        "frequency": "monthly",
        "next_due_date": "2026-10-15",
        "status": "active",
        "notes": "Shared with household. Auto-renews on primary credit card.",
    },
    {
        "id": "sub_002",
        "name": "Spotify Family Plan",
        "category": "subscription",
        "cost": 16.99,
        "frequency": "monthly",
        "next_due_date": "2026-10-01",
        "status": "active",
        "notes": "Primary account linked to household email.",
    },
    {
        "id": "maint_001",
        "name": "Tesla Model 3 Tire Rotation",
        "category": "vehicle_maintenance",
        "cost": 65.00,
        "frequency": "every 6,250 miles",
        "next_due_date": "2026-11-01",
        "status": "pending",
        "notes": "Service center or local tire shop.",
    },
    {
        "id": "maint_002",
        "name": "Home HVAC Air Filter Replacement",
        "category": "home_maintenance",
        "cost": 35.00,
        "frequency": "quarterly",
        "next_due_date": "2026-10-30",
        "status": "pending",
        "notes": "Size: 20x25x1 MERV 11 filter.",
    },
]


def seed():
    print(f"Connecting to Firestore for project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection(COLLECTION_NAME)

    for item in SEED_ITEMS:
        doc_id = item["id"]
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(item)
        print(f"Seeded document [{doc_id}]: {item['name']}")

    print("✅ Firestore seeding completed successfully!")


if __name__ == "__main__":
    seed()
