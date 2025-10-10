import logging
from datetime import datetime
import pytz
import stripe

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


from accounts.models import Profile
from .models import Subscription

# Config Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


# ============================================================
# ===============   ABONNEMENTS STRIPE   =====================
# ============================================================

@login_required
def subscription(request):
    profile = request.user.profile
    status = profile.service  # 'Yaya' ou 'Parent'

    active_subscription = Subscription.objects.filter(user=request.user, is_active=True).first()

    #product_ids = {
    #    'Yaya': 'prod_SnxoCNepc3XzFh',
    #    'Parent': 'prod_SnxmIb87vsH2dh',
    #}
    #product_id = product_ids.get(status)

    lookup_keys = {
        'Yaya': 'yaya_annual_2e',
        'Parent': 'parent_annual_99e',
        #'Yaya': 'yaya_test_0e',

    }
    lookup_key = lookup_keys.get(status)
       
    #product = stripe.Product.retrieve(product_id)
    #prices = stripe.Price.list(product=product_id)
    prices = stripe.Price.list(lookup_keys=[lookup_key], expand=["data.product"])
    price = prices.data[0]
    product = price.product
    product_price = price.unit_amount / 100.0

    return render(request, 'stripe_sub/subscription.html', {
        'status': status,
        'product': product,
        'price': price,
        'product_price': product_price,
        'active_subscription': active_subscription,
    })


@login_required
def create_checkout_session(request):
    profile = request.user.profile
    status = profile.service
    price_id = request.POST.get('price_id')

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode="subscription",
        line_items=[{'price': price_id, 'quantity': 1}],
        customer_email=request.user.email,
        success_url=request.build_absolute_uri('/subscription/success/') + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri('/subscription/cancel/'),
        metadata={"user_id": request.user.id}  # ✅ obligatoire
    )

    print(f"✅ Checkout session créée : {checkout_session.id} pour user={request.user.id}")


    return redirect(checkout_session.url, code=303)


@login_required
def payment_successful(request):
    subscription = Subscription.objects.filter(user=request.user, is_active=True).order_by('-current_period_end').first()
    if subscription:
        print(f"DEBUG Abonnement trouvé en DB: {subscription}")
        return render(request, "stripe_sub/payment_successful.html", {
            "product": subscription.product_name,
            "price": subscription.price,
            "start_date": subscription.current_period_start,
            "end_date": subscription.current_period_end,
            "is_active": subscription.is_active,
            "payment_type": "Abonnement",
        })

    session_id = request.GET.get("session_id")
    if not session_id:
        return render(request, "stripe_sub/payment_successful.html", {
            "error": "Abonnement en cours de traitement, réessayez dans quelques secondes."
        })

    try:
        # Récupère la session complète
        session = stripe.checkout.Session.retrieve(session_id)
        subscription_id = session.get("subscription")
        if not subscription_id:
            raise ValueError("Aucun abonnement associé à cette session Stripe.")

        # Récupère l'abonnement complet
        stripe_sub = stripe.Subscription.retrieve(subscription_id)
        print(f"DEBUG Stripe subscription: {stripe_sub}")

        # Sauvegarde en DB
        _save_or_update_subscription(sub=stripe_sub, customer_id=session.customer, user_id=request.user.id)

        subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
        print(f"DEBUG Abonnement après sauvegarde DB: {subscription}")

        return render(request, "stripe_sub/payment_successful.html", {
            "product": subscription.product_name,
            "price": subscription.price,
            "start_date": subscription.current_period_start,
            "end_date": subscription.current_period_end,
            "is_active": subscription.is_active,
            "payment_type": "Abonnement",
        })
    except Exception as e:
        print(f"ERROR récupération Stripe subscription: {e}")
        return render(request, "stripe_sub/payment_successful.html", {
            "error": f"Impossible de récupérer l’abonnement Stripe : {e}"
        })



def payment_cancelled(request):
    return render(request, 'stripe_sub/payment_cancelled.html')

# -----------------------------
# Sauvegarde ou mise à jour de l'abonnement
# -----------------------------
def _save_or_update_subscription(sub, customer_id, user_id):
    try:
        user = get_user_model().objects.get(id=user_id)
        profile = Profile.objects.get(user=user)

        # Log complet pour debug
        print(f"DEBUG Stripe subscription raw: {sub}")

        # ⚡ Récupère le premier item de l'abonnement
        sub_item = sub["items"]["data"][0]

        # Récupère le prix et le produit
        price_obj = stripe.Price.retrieve(sub_item["price"]["id"])
        product_obj = stripe.Product.retrieve(price_obj.product)

        print(f"DEBUG Price récupéré : {price_obj.id}, montant={price_obj.unit_amount}")
        print(f"DEBUG Produit récupéré : {product_obj.id}, nom={product_obj.name}")

        # ⚡ Récupère correctement les dates depuis l'item
        start_ts = sub_item.get("current_period_start")
        end_ts = sub_item.get("current_period_end")
        current_period_start = datetime.fromtimestamp(start_ts, tz=pytz.UTC) if start_ts else None
        current_period_end = datetime.fromtimestamp(end_ts, tz=pytz.UTC) if end_ts else None

        print(f"DEBUG Dates converties: start={current_period_start}, end={current_period_end}")

        # Nom et prénom vérifiés
        first_name = profile.verified_first_name or user.first_name
        last_name = profile.verified_last_name or user.last_name

        # Sauvegarde ou mise à jour de l'abonnement
        subscription, created = Subscription.objects.update_or_create(
            stripe_subscription_id=sub["id"],
            defaults={
                "user": user,
                "first_name": first_name,
                "last_name": last_name,
                "product_name": product_obj.name,
                "price": price_obj.unit_amount / 100,
                "is_active": sub.get("status") in ["active", "trialing"],
                "current_period_start": current_period_start,
                "current_period_end": current_period_end,
                "stripe_customer_id": customer_id,
            }
        )

        print(f"DEBUG Abonnement sauvegardé en DB: created={created}, sub_id={sub['id']}")

    except Exception as e:
        print(f"ERROR _save_or_update_subscription: {e}", e)





# ============================================================
# ===============   STRIPE IDENTITY   ========================
# ============================================================

@login_required
def create_verification_session(request):
    if request.method == "POST":
        try:
            session = stripe.identity.VerificationSession.create(
                verification_flow=settings.STRIPE_IDENTITY_FLUX,
                return_url=request.build_absolute_uri("/identity/complete/"),
                metadata={"user_id": str(request.user.id)},
            )
            print(f"✅ Session Stripe Identity créée : {session.id} pour user_id={request.user.id}")
            return redirect(session.url)
        except Exception as e:
            print("❌ Erreur lors de la création de session Stripe Identity", exc_info=True)
            messages.error(request, "Impossible de démarrer la vérification pour le moment.")
            return redirect("accounts:profile")

    return redirect("accounts:profile")


@login_required
def identity_complete(request):
    profile = request.user.profile
    return render(request, "stripe_sub/identity_complete.html", {
        "is_verified": profile.ci_is_verified,
        "first_name": profile.verified_first_name,
        "last_name": profile.verified_last_name,
    })


# ============================================================
# ===============   STRIPE WEBHOOK   =========================
# ============================================================

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Webhook Stripe principal : gère Identity + Abonnements."""
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        print(f"🔔 Webhook Stripe reçu : {event['type']}")
        event_type = event["type"]

        # ==========================================================
        # 🧩 1. Stripe Identity : vérification d’identité
        # ==========================================================
        if event_type == "identity.verification_session.verified":
            _handle_identity_success(event["data"]["object"])

        elif event_type in [
            "identity.verification_session.requires_input",
            "identity.verification_session.canceled",
        ]:
            reason = "requires_input" if event_type.endswith("requires_input") else "canceled"
            _handle_identity_failure(event["data"]["object"], reason=reason)

        # ==========================================================
        # 💳 2. Checkout terminé (nouvel abonnement)
        # ==========================================================
        elif event_type == "checkout.session.completed":
            session = event["data"]["object"]
            subscription_id = session.get("subscription")
            customer_id = session.get("customer")
            metadata = session.get("metadata", {})
            user_id = _get_user_id_from_customer(customer_id, metadata)
        
            print(f"checkout.session.completed → subscription_id={subscription_id}, user_id={user_id}")
        
            # ⚡ Met à jour le profil avec stripe_customer_id
            if user_id and customer_id:
                _update_profile_customer_id(user_id, customer_id)
        
            # Enregistre ou met à jour l’abonnement
            if subscription_id and user_id:
                stripe_sub = stripe.Subscription.retrieve(subscription_id)
                _save_or_update_subscription(stripe_sub, customer_id, user_id)
        
        # ==========================================================
        # 🔁 3. Abonnement créé ou mis à jour (modification, renouvellement…)
        # ==========================================================
        elif event_type in ["customer.subscription.created", "customer.subscription.updated"]:
            sub = event["data"]["object"]
            customer_id = sub.get("customer")
            metadata = sub.get("metadata", {})
            user_id = _get_user_id_from_customer(customer_id, metadata)
            status = sub.get("status")
        
            print(f"📦 Subscription updated: {sub['id']} (status={status})")
        
            if not user_id:
                print(f"⚠️ Impossible de retrouver l'utilisateur pour customer={customer_id}")
            else:
                # Si l'abonnement est annulé ou en échec, désactive-le
                if status in ["canceled", "incomplete_expired", "past_due", "unpaid"]:
                    Subscription.objects.filter(stripe_subscription_id=sub["id"]).update(is_active=False)
                    print(f"⚠️ Abonnement désactivé (status={status}) : {sub['id']}")
                else:
                    # Sinon, mise à jour complète (dates, produit, prix, statut)
                    stripe_sub = stripe.Subscription.retrieve(sub["id"])
                    _save_or_update_subscription(stripe_sub, customer_id, user_id)
                    print(f"✅ Abonnement mis à jour pour user_id={user_id}, status={status}")
        
        # ==========================================================
        # 💰 4. Paiement automatique réussi (renouvellement)
        # ==========================================================
        elif event_type == "invoice.payment_succeeded":
            invoice = event["data"]["object"]
            subscription_id = invoice.get("subscription")
            customer_id = invoice.get("customer")
        
            print(f"💰 Paiement réussi pour subscription={subscription_id}")
        
            if subscription_id and customer_id:
                try:
                    stripe_sub = stripe.Subscription.retrieve(subscription_id)
                    profile = Profile.objects.get(stripe_customer_id=customer_id)
                    user_id = profile.user.id
                    _save_or_update_subscription(stripe_sub, customer_id, user_id)
                    print(f"✅ Abonnement mis à jour après paiement réussi pour user_id={user_id}")
                except Profile.DoesNotExist:
                    print(f"❌ Aucun profil trouvé pour customer_id={customer_id}")
                except Exception as e:
                    print(f"⚠️ Erreur lors du traitement de invoice.payment_succeeded : {e}", exc_info=True)
        
        # ==========================================================
        # ❌ 5. Abonnement supprimé
        # ==========================================================
        elif event_type == "customer.subscription.deleted":
            sub = event["data"]["object"]
            Subscription.objects.filter(stripe_subscription_id=sub["id"]).update(is_active=False)
            print(f"⚠️ Abonnement supprimé : {sub['id']}")
        

    except Exception as e:
        print(f"❌ Erreur webhook Stripe : {e}", exc_info=True)
        return HttpResponse("Webhook error", status=500, content_type="text/plain")

    return HttpResponse("OK", status=200, content_type="text/plain")


# ==========================================================
# 🧩 Fonctions utilitaires
# ==========================================================

def _get_user_id_from_customer(customer_id, metadata):
    """Retourne user_id à partir de metadata ou du stripe_customer_id."""
    user_id = metadata.get("user_id")
    if user_id:
        return user_id
    try:
        profile = Profile.objects.get(stripe_customer_id=customer_id)
        return profile.user.id
    except Profile.DoesNotExist:
        print(f"⚠️ Aucun profil trouvé pour customer_id={customer_id}")
        return None


def _update_profile_customer_id(user_id, customer_id):
    """Associe stripe_customer_id au profil utilisateur."""
    try:
        user = get_user_model().objects.get(id=user_id)
        profile = Profile.objects.get(user=user)
        profile.stripe_customer_id = customer_id
        profile.save()
        print(f"💾 Profile mis à jour avec stripe_customer_id={customer_id}")
    except Exception as e:
        print(f"❌ Impossible de mettre à jour le profil user_id={user_id} : {e}", exc_info=True)


def _handle_identity_success(session):
    """Marque le profil comme vérifié via Stripe Identity."""
    print("🔔 [Stripe Identity] Session vérifiée")

    user_id = session.get("metadata", {}).get("user_id")
    if not user_id:
        print("❌ user_id manquant dans metadata Stripe Identity")
        return

    try:
        User = get_user_model()
        user = User.objects.get(id=user_id)
        profile = Profile.objects.get(user=user)
    except Exception as e:
        print(f"❌ Impossible de récupérer User/Profile pour user_id={user_id} : {e}")
        return

    profile.ci_is_verified = True

    try:
        report_id = session.get("last_verification_report")
        if report_id:
            print(f"📄 Récupération du rapport {report_id}")
            report = stripe.identity.VerificationReport.retrieve(report_id)
            document = report.get("document", {})

            profile.verified_first_name = document.get("first_name") or ""
            profile.verified_last_name = document.get("last_name") or ""

            print(f"✅ Nom vérifié pour user_id={user_id} : "
                        f"{profile.verified_first_name} {profile.verified_last_name}")
        else:
            print(f"⚠️ Aucun rapport trouvé dans session pour user_id={user_id}")

    except Exception as e:
        print(f"⚠️ Erreur récupération rapport Stripe Identity : {e}", exc_info=True)

    try:
        profile.save()
        print(f"💾 Profil mis à jour pour user_id={user_id}")
    except Exception as e:
        print(f"❌ Impossible de sauvegarder le profil user_id={user_id} : {e}", exc_info=True)


def _handle_identity_failure(session, reason):
    """Marque la vérification d’identité comme échouée ou annulée."""
    print(f"⚠️ Vérification Identity échouée ({reason})")
    user_id = session.get("metadata", {}).get("user_id")
    if not user_id:
        print("❌ user_id manquant dans metadata Stripe Identity")
        return
    try:
        User = get_user_model()
        user = User.objects.get(id=user_id)
        profile = Profile.objects.get(user=user)
        profile.ci_is_verified = False
        profile.save()
        print(f"💾 Profil mis à jour (échec vérification) pour user_id={user_id}")
    except Exception as e:
        print(f"❌ Impossible de mettre à jour profil après échec Identity : {e}", exc_info=True)
