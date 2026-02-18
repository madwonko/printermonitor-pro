"""
Seed License Tiers

Initialize the database with license tier data
"""

from sqlalchemy.orm import Session
from ..models import LicenseTier


def seed_license_tiers(db: Session):
    """Create default license tiers"""
    
    tiers = [
        {
            'id': 'free',
            'name': 'Free',
            'price_monthly': 0,
            'price_yearly': 0,
            'max_devices': 1,
            'max_printers': 3,
            'history_days': 7,
            'features': ['basic_alerts']
        },
        {
            'id': 'maker',
            'name': 'Maker',
            'price_monthly': 1000,  # $10.00
            'price_yearly': 10000,  # $100.00 ($8.33/mo - 17% discount)
            'max_devices': 2,
            'max_printers': 10,
            'history_days': 90,
            'features': ['basic_alerts', 'advanced_alerts', 'email_notifications']
        },
        {
            'id': 'pro',
            'name': 'Pro',
            'price_monthly': 5000,  # $50.00
            'price_yearly': 50000,  # $500.00 ($41.67/mo - 17% discount)
            'max_devices': 5,
            'max_printers': 50,
            'history_days': 365,
            'features': ['basic_alerts', 'advanced_alerts', 'email_notifications', 'api_access', 'webhooks']
        },
        {
            'id': 'enterprise',
            'name': 'Enterprise',
            'price_monthly': 15000,  # $150.00
            'price_yearly': 150000,  # $1,500.00 ($125/mo - 17% discount)
            'max_devices': 10,
            'max_printers': -1,  # Unlimited
            'history_days': -1,  # Unlimited
            'features': ['basic_alerts', 'advanced_alerts', 'email_notifications', 'api_access', 'webhooks', 'priority_support', 'sla']
        }
    ]
    
    for tier_data in tiers:
        # Check if tier already exists
        existing = db.query(LicenseTier).filter(LicenseTier.id == tier_data['id']).first()
        
        if not existing:
            tier = LicenseTier(**tier_data)
            db.add(tier)
            print(f"✓ Created tier: {tier.name}")
        else:
            print(f"  Tier already exists: {existing.name}")
    
    db.commit()
    print("✓ License tiers seeded")
