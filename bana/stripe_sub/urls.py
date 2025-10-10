from django.urls import path

from . import views

urlpatterns = [
    path('subscription/', views.subscription, name='subscription'),
    path("checkout/", views.create_checkout_session, name="create_checkout_session"),
    path("subscription/success/", views.payment_successful, name="payment_successful"),
    path("subscription/cancel/", views.payment_cancelled, name="payment_cancelled"),
    path("identity/", views.create_verification_session, name="create_verification_session"),
    path("identity/complete/", views.identity_complete, name="identity_complete"),
    #path("webhook/stripe/", views.stripe_webhook, name="stripe_webhook"),
]
