import stripe

from config import settings
from abc import ABC, abstractmethod


stripe.api_key = settings.Settings().STRIPE_SECRET_KEY


class PaymentInterface(ABC):
    @abstractmethod
    def create_session(self, order, user):
        pass


class StripePayment(PaymentInterface):
    def __init__(self, line_items):
        self.line_items = line_items

    def create_session(self, order, user):
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            customer_email=user.email,
            line_items=self.line_items,
            success_url="http://127.0.0.1:8000/api/v1/payments/success/",
            cancel_url="http://127.0.0.1:8000/api/v1/payments/cancel/",
        )

        return session
