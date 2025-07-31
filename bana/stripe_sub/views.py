import logging
from django.contrib  import messages
from accounts.models import Profile
import stripe
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import *
from django.utils import timezone
from datetime import datetime, timedelta
import pytz
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def subscription(request):
    profile = request.user.profile
    status = profile.service  # 'yaya' ou 'parent'

    # Associer les bons IDs selon le rôle
    product_ids = {
        'yaya': 'prod_SlMhIVC2sprior',
        'parent': 'prod_SlKb8ZQdG6holQ',
    }

    product_id = product_ids.get(status)

    if not product_id:
        return render(request, 'stripe/error.html', {'message': "Statut utilisateur inconnu."})

    product = stripe.Product.retrieve(product_id)
    prices = stripe.Price.list(product=product_id)
    price = prices.data[0]  # suppose qu’il y a 1 seul prix par produit
    product_price = price.unit_amount / 100.00

    return render(request, 'stripe_sub/subscription.html', {
        'product': product,
        'price': price,
        'product_price': product_price,
        'status': status
    })
    
@login_required
def create_checkout_session(request):    
    profile = request.user.profile
    status = profile.service  # 'yaya' ou 'parent'
    price_id = request.POST.get('price_id')

    # Récupérer les infos du prix pour connaître son type
    price = stripe.Price.retrieve(price_id)

    # Déterminer automatiquement le mode de paiement
    mode = 'subscription' if price.recurring is not None else 'payment'

    # Créer la session Stripe Checkout
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode=mode,
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        customer_email=request.user.email,
        success_url = request.build_absolute_uri('/subscription/success/') + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url = request.build_absolute_uri('/subscription/cancel/') + '?session_id={CHECKOUT_SESSION_ID}',
        metadata={
            "user_id": request.user.id,
            "status": status,
        }
    )

    return redirect(checkout_session.url, code=303)


@login_required
def payment_successful(request):
    session_id = request.GET.get('session_id')

    if not session_id:
        return render(request, 'stripe_sub/payment_successful.html', {'error': "Session ID manquant."})

    try:
        # 1. Récupérer la session Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        customer_id = session.customer
        subscription_id = session.subscription  # None pour les paiements uniques
        user = request.user

        # 2. Ligne de commande Stripe
        line_item = stripe.checkout.Session.list_line_items(session_id).data[0]
        price = line_item.amount_total / 100
        product_name = line_item.description

        # 3. Gestion des dates selon le type de paiement
        current_period_start = timezone.now()
        current_period_end = None
        is_active = True

        print(f"🔍 Session mode: {session.mode}")
        print(f"🔍 Subscription ID: {subscription_id}")

        if subscription_id:
            # CAS 1: Abonnement récurrent (parent - 99€/an)
            print("📋 Traitement d'un abonnement récurrent")
            subscription = stripe.Subscription.retrieve(subscription_id)

            # Debug: afficher toutes les propriétés de l'abonnement
            print(f"🧪 Données brutes subscription:")
            print(f"  - current_period_start: {subscription.current_period_start}")
            print(f"  - current_period_end: {subscription.current_period_end}")
            print(f"  - status: {subscription.status}")
            print(f"  - billing_cycle_anchor: {getattr(subscription, 'billing_cycle_anchor', 'N/A')}")

            # Conversion sécurisée des timestamps avec timezone
            if subscription.current_period_start:
                current_period_start = datetime.fromtimestamp(
                    subscription.current_period_start, 
                    tz=pytz.UTC
                )
            
            if subscription.current_period_end:
                current_period_end = datetime.fromtimestamp(
                    subscription.current_period_end, 
                    tz=pytz.UTC
                )
            else:
                # CORRECTION: Si pas de current_period_end, calculer selon l'intervalle
                print("⚠️ current_period_end est None, calcul manuel...")
                
                # Récupérer les infos du prix pour connaître l'intervalle
                subscription_item = subscription['items']['data'][0]
                price = stripe.Price.retrieve(subscription_item.price.id)
                
                print(f"🔍 Intervalle de facturation: {price.recurring.interval}")
                print(f"🔍 Nombre d'intervalles: {price.recurring.interval_count}")
                
                # Calculer la date de fin selon l'intervalle
                if price.recurring.interval == 'year':
                    current_period_end = current_period_start + timedelta(days=365 * price.recurring.interval_count)
                elif price.recurring.interval == 'month':
                    current_period_end = current_period_start + timedelta(days=30 * price.recurring.interval_count)
                elif price.recurring.interval == 'day':
                    current_period_end = current_period_start + timedelta(days=price.recurring.interval_count)
                
                print(f"📅 Date de fin calculée: {current_period_end}")

            # Vérification de l'état actif
            is_active = subscription.status in ['active', 'trialing']
            
            print(f"📅 Période début: {current_period_start}")
            print(f"📅 Période fin: {current_period_end}")
            print(f"📊 Statut Stripe: {subscription.status}")

        else:
            # CAS 2: Paiement unique (yaya - 2€)
            print("💰 Traitement d'un paiement unique")
            
            # Pour un paiement unique, on définit une durée arbitraire
            # ou on considère que c'est valide indéfiniment
            current_period_start = timezone.now()
            
            # Option 1: Valide pour 1 an
            current_period_end = current_period_start + timedelta(days=365)
            
            # Option 2: Pas de date de fin (valide indéfiniment)
            # current_period_end = None
            
            is_active = True
            
            print(f"📅 Paiement unique - Début: {current_period_start}")
            print(f"📅 Paiement unique - Fin: {current_period_end}")

        # 4. Enregistrement en base
        subscription_obj, created = Subscription.objects.update_or_create(
            user=user,
            stripe_subscription_id=subscription_id or f"payment_{session_id}",  # ID unique même pour paiements
            defaults={
                'stripe_customer_id': customer_id,
                'product_name': product_name,
                'price': price,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': is_active,
                'current_period_start': current_period_start,
                'current_period_end': current_period_end,
            }
        )

        print(f"✅ Abonnement {'créé' if created else 'mis à jour'}: {subscription_obj.id}")
        print(f"🏁 Date de fin enregistrée: {subscription_obj.current_period_end}")

        return render(request, 'stripe_sub/payment_successful.html', {
            'subscription': subscription_id,
            'start_date': current_period_start,
            'end_date': current_period_end,
            'product': product_name,
            'is_subscription': bool(subscription_id),
            'payment_type': 'Abonnement récurrent' if subscription_id else 'Paiement unique'
        })

    except Exception as e:
        print("❌ ERREUR pendant enregistrement :", str(e))
        print("❌ Type d'erreur :", type(e).__name__)
        import traceback
        traceback.print_exc()
        return render(request, 'stripe_sub/payment_successful.html', {'error': str(e)})   
           

def payment_cancelled(request):
    return render(request, 'stripe_sub/payment_cancelled.html')


@login_required
def create_verification_session(request):
    
    if request.method == "POST":
        session = stripe.identity.VerificationSession.create(
            type="document",
            return_url="http://37.187.94.53:9758/identity/complete/",
            metadata={
                "user_id": str(request.user.id)
            }
        )
        return redirect(session.url)
    return redirect("accounts:profile") 
    
    
@login_required
def identity_complete(request):
    if request.user.profile.ci_is_verified:
        messages.success(request, "Votre identité a été vérifiée avec succès.")
    else:
        messages.error(request, "Votre vérification est en cours ou a échoué. Veuillez réessayer plus tard.")
    return render(request, 'stripe_sub/identity_complete.html') 


@csrf_exempt
def stripe_webhook(request):
    try:
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)

        if event["type"] == "identity.verification_session.verified":
            session = event["data"]["object"]
            user_id = session.get("metadata", {}).get("user_id")

            if user_id is None:
                raise ValueError("user_id manquant dans metadata Stripe.")

            User = get_user_model()
            user = User.objects.get(id=user_id)
            profile = Profile.objects.get(user=user)

            profile.ci_is_verified = True
            
            # Récupération des données d’identité
            report_id = session.get("last_verification_report")
            if report_id:
                report = stripe.identity.VerificationReport.retrieve(report_id)
                document = report.get("document", {})

                profile.verified_first_name = document.get("first_name")
                profile.verified_last_name = document.get("last_name")
                profile.verified_address = document.get("address")
                profile.verified_dob = document.get("dob")
                # Récupérer l’image temporaire de la pièce d’identité
                front_id = document.get("front")
                if front_id:
                    file = stripe.File.retrieve(front_id)
                    profile.document_image_url = file.get("url")
                    
            profile.save()

    except Exception as e:
        return HttpResponse("Webhook error", status=500, content_type="text/plain")

    return HttpResponse("OK", status=200, content_type="text/plain")
