"""
Billing Routes

Stripe checkout and subscription management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import stripe

from ..database import get_db
from ..models import User
from ..auth.dependencies import get_current_user
from ..utils.stripe_service import StripeService
from ..config import settings

router = APIRouter()


class CheckoutRequest(BaseModel):
    """Request to create checkout session"""
    tier_id: str  # 'maker', 'pro', 'enterprise'
    billing_period: str  # 'monthly', 'yearly'


@router.post("/create-checkout-session")
def create_checkout_session(
    checkout_data: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a Stripe Checkout Session for subscription upgrade
    
    Returns URL to redirect user to Stripe checkout
    """
    # Validate tier
    valid_tiers = ['maker', 'pro', 'enterprise']
    if checkout_data.tier_id not in valid_tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier. Must be one of: {valid_tiers}"
        )
    
    # Validate billing period
    if checkout_data.billing_period not in ['monthly', 'yearly']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Billing period must be 'monthly' or 'yearly'"
        )
    
    # Create checkout session
    checkout_url = StripeService.create_checkout_session(
        user=current_user,
        tier_id=checkout_data.tier_id,
        billing_period=checkout_data.billing_period,
        success_url=f"{settings.API_V1_PREFIX}/billing/success",
        cancel_url=f"{settings.API_V1_PREFIX}/billing/cancel"
    )
    
    if not checkout_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )
    
    return {"checkout_url": checkout_url}


@router.get("/success")
def checkout_success():
    """Checkout success page"""
    return {
        "message": "Payment successful! Your subscription is now active.",
        "next_steps": "You can now use all features of your new plan."
    }


@router.get("/cancel")
def checkout_cancel():
    """Checkout cancelled page"""
    return {
        "message": "Checkout cancelled",
        "note": "No charges were made. You can try again anytime."
    }


@router.post("/cancel-subscription")
def cancel_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel current subscription
    Will revert to Free tier at end of billing period
    """
    if not current_user.license or not current_user.license.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found"
        )
    
    success = StripeService.cancel_subscription(
        current_user.license.stripe_subscription_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )
    
    return {"message": "Subscription cancelled successfully"}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Stripe webhook handler
    
    Handles subscription events from Stripe
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    event_type = event['type']
    data = event['data']['object']
    
    if event_type == 'customer.subscription.created':
        StripeService.handle_subscription_created(db, data)
    
    elif event_type == 'customer.subscription.updated':
        StripeService.handle_subscription_updated(db, data)
    
    elif event_type == 'customer.subscription.deleted':
        StripeService.handle_subscription_deleted(db, data)
    
    else:
        print(f"Unhandled event type: {event_type}")
    
    return {"status": "success"}
