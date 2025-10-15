import stripe

from config import settings
from abc import ABC, abstractmethod


stripe.api_key = settings.Settings.STRIPE_SECRET_KEY


class PaymentInterface(ABC):
    @abstractmethod
    def create_session(self, order, user):
        pass


class StripePayment(PaymentInterface):
    def __init__(self, line_items):
        self.line_items= line_items

    def create_session(self, order, user):
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            customer_email=user.email,
            line_items=self.line_items,
            success_url="http://localhost:8000/payments/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:8000/payments/cancel",
        )

        return session
