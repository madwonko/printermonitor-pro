"""
Stripe Service

Handles Stripe API interactions for subscriptions
"""

import stripe
from sqlalchemy.orm import Session
from typing import Optional, Dict
from datetime import datetime, timedelta

from ..config import settings
from ..models import User, License


class StripeService:
    """Stripe payment service"""
    
    @staticmethod
    def create_checkout_session(
        user: User,
        tier_id: str,
        billing_period: str,
        success_url: str,
        cancel_url: str
    ) -> Optional[str]:
        """Create a Stripe Checkout Session"""
        
        # Set API key HERE inside the function
        stripe.api_key = "sk_test_51T2HcxPnfYjoQPTjMBzZ8LHjE9Dyz8hRI7cJOq1ojFvW9QwM0ud5J7L7TV8KmqdtQMp6WvCFzLGZZYtuTPE64md002LnHnveS"
        
        price_map = {
            ('maker', 'monthly'): settings.STRIPE_PRICE_MAKER_MONTHLY,
            ('maker', 'yearly'): settings.STRIPE_PRICE_MAKER_YEARLY,
            ('pro', 'monthly'): settings.STRIPE_PRICE_PRO_MONTHLY,
            ('pro', 'yearly'): settings.STRIPE_PRICE_PRO_YEARLY,
            ('enterprise', 'monthly'): settings.STRIPE_PRICE_ENTERPRISE_MONTHLY,
            ('enterprise', 'yearly'): settings.STRIPE_PRICE_ENTERPRISE_YEARLY,
        }
        
        price_id = price_map.get((tier_id, billing_period))
        if not price_id:
            raise ValueError(f"Invalid tier or billing period: {tier_id}, {billing_period}")
        
        try:
            if user.license and user.license.stripe_customer_id:
                customer_id = user.license.stripe_customer_id
            else:
                customer = stripe.Customer.create(
                    email=user.email,
                    name=user.full_name,
                    metadata={'user_id': user.id}
                )
                customer_id = customer.id
            
            session = stripe.checkout.Session.create(
                customer=customer_id,
                mode='subscription',
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user.id,
                    'tier_id': tier_id
                }
            )
            
            return session.url
            
        except stripe.error.StripeError as e:
            print(f"✗ Stripe error: {e}")
            return None
    
    @staticmethod
    def handle_subscription_created(db: Session, subscription_data: Dict):
        """Handle subscription.created webhook"""
        # ... rest of methods unchanged
        pass
    
    @staticmethod
    def handle_subscription_updated(db: Session, subscription_data: Dict):
        pass
    
    @staticmethod
    def handle_subscription_deleted(db: Session, subscription_data: Dict):
        pass
    
    @staticmethod
    def cancel_subscription(subscription_id: str) -> bool:
        pass
