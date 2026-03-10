from django.urls import path

from . import views

urlpatterns = [
    path('abonnement/', views.subscription, name='subscription'),
    path("checkout/", views.create_checkout_session, name="create_checkout_session"),
    path("abonnement/réussie/", views.payment_successful, name="payment_successful"),
    path("abonnement/annulé/", views.payment_cancelled, name="payment_cancelled"),
    path("identité/", views.create_verification_session, name="create_verification_session"),
    path("identité/complete/", views.identity_complete, name="identity_complete"),
    #path("webhook/stripe/", views.stripe_webhook, name="stripe_webhook"),
]
