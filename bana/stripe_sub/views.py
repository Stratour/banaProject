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

    product_ids = {
        'Yaya': 'prod_SnxoCNepc3XzFh',
        'Parent': 'prod_SnxmIb87vsH2dh',
    }
    product_id = product_ids.get(status)

    product = stripe.Product.retrieve(product_id)
    prices = stripe.Price.list(product=product_id)
    price = prices.data[0]
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

    logger.debug(f"✅ Checkout session créée : {checkout_session.id} pour user={request.user.id}")


    return redirect(checkout_session.url, code=303)


@login_required
def payment_successful(request):
    subscription = Subscription.objects.filter(user=request.user, is_active=True).order_by('-current_period_end').first()

    if not subscription:
        return render(request, "stripe_sub/payment_successful.html", {
            "error": "Abonnement en cours de traitement, réessayez dans quelques secondes."
        })

    return render(request, "stripe_sub/payment_successful.html", {
        "product": subscription.product_name,
        "price": subscription.price,
        "start_date": subscription.current_period_start,
        "end_date": subscription.current_period_end,
        "is_active": subscription.is_active,
        "payment_type": "Abonnement",
    })


def payment_cancelled(request):
    return render(request, 'stripe_sub/payment_cancelled.html')


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
            logger.info(f"✅ Session Stripe Identity créée : {session.id} pour user_id={request.user.id}")
            return redirect(session.url)
        except Exception as e:
            logger.error("❌ Erreur lors de la création de session Stripe Identity", exc_info=True)
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
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        logger.info(f"🔔 Webhook Stripe reçu : {event['type']}")

        # -------- Identity --------
        if event["type"] == "identity.verification_session.verified":
            session = event["data"]["object"]
            _handle_identity_success(session)

        elif event["type"] == "identity.verification_session.requires_input":
            session = event["data"]["object"]
            _handle_identity_failure(session, reason="requires_input")

        elif event["type"] == "identity.verification_session.canceled":
            session = event["data"]["object"]
            _handle_identity_failure(session, reason="canceled")

        # -------- Abonnements --------

        elif event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            subscription_id = session.get("subscription")
            customer_id = session.get("customer")
            user_id = session.get("metadata", {}).get("user_id")

            logger.info(f"checkout.session.completed → subscription_id={subscription_id}, user_id={user_id}")

            # ⚡ Mettre à jour le profile avec stripe_customer_id
            if user_id and customer_id:
                try:
                    user = get_user_model().objects.get(id=user_id)
                    profile = Profile.objects.get(user=user)
                    profile.stripe_customer_id = customer_id
                    profile.save()
                    logger.info(f"💾 Profile mis à jour avec stripe_customer_id={customer_id}")
                except Exception as e:
                    logger.error(f"❌ Impossible de mettre à jour le profil user_id={user_id} : {e}", exc_info=True)

            # Si subscription_id présent, enregistrer l'abonnement
            if subscription_id and user_id:
                stripe_sub = stripe.Subscription.retrieve(subscription_id)
                _save_or_update_subscription(stripe_sub, customer_id, user_id)

        elif event["type"] in ["customer.subscription.created", "customer.subscription.updated"]:
            sub = event["data"]["object"]
            customer_id = sub.get("customer")
            user_id = sub.get("metadata", {}).get("user_id")

            # Fallback si metadata manquant : retrouver via stripe_customer_id
            if not user_id and customer_id:
                try:
                    profile = Profile.objects.get(stripe_customer_id=customer_id)
                    user_id = profile.user.id
                except Profile.DoesNotExist:
                    logger.error(f"❌ Impossible de retrouver user_id pour customer={customer_id}")

            if user_id:
                _save_or_update_subscription(sub, customer_id, user_id)

        elif event["type"] == "customer.subscription.deleted":
            sub = event["data"]["object"]
            Subscription.objects.filter(stripe_subscription_id=sub["id"]).update(is_active=False)
            logger.info(f"⚠️ Abonnement supprimé : {sub['id']}")

    except Exception as e:
        logger.error(f"❌ Erreur webhook Stripe : {e}", exc_info=True)
        return HttpResponse("Webhook error", status=500, content_type="text/plain")

    return HttpResponse("OK", status=200, content_type="text/plain")



# -----------------------------
# Sauvegarde ou mise à jour de l'abonnement
# -----------------------------
def _save_or_update_subscription(sub, customer_id, user_id):
    try:
        user = get_user_model().objects.get(id=user_id)
        profile = Profile.objects.get(user=user)

        # ⚡ Produit et prix
        sub_item = sub["items"]["data"][0]
        price_obj = stripe.Price.retrieve(sub_item["price"]["id"])
        product_obj = stripe.Product.retrieve(price_obj.product)

        # Dates
        start_ts = sub.get("current_period_start")
        end_ts = sub.get("current_period_end")

        current_period_start = datetime.fromtimestamp(start_ts, tz=pytz.UTC) if start_ts else None
        current_period_end = datetime.fromtimestamp(end_ts, tz=pytz.UTC) if end_ts else None

        # ⚡ Nom et prénom vérifiés
        first_name = profile.verified_first_name or user.first_name
        last_name = profile.verified_last_name or user.last_name

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

        logger.info(f"💾 Abonnement mis à jour en DB sub_id={sub['id']}, user_id={user_id}, created={created}, start={current_period_start}, end={current_period_end}")

    except Exception as e:
        logger.error(f"⚠️ Erreur sauvegarde abonnement sub_id={sub.get('id')} : {e}", exc_info=True)


def _handle_identity_success(session):
    logger.info("🔔 [Stripe Identity] Session vérifiée")

    user_id = session.get("metadata", {}).get("user_id")
    if not user_id:
        logger.error("❌ user_id manquant dans metadata Stripe Identity")
        return

    try:
        User = get_user_model()
        user = User.objects.get(id=user_id)
        profile = Profile.objects.get(user=user)
    except Exception as e:
        logger.error(f"❌ Impossible de récupérer User/Profile pour user_id={user_id} : {e}")
        return

    profile.ci_is_verified = True

    try:
        report_id = session.get("last_verification_report")
        if report_id:
            logger.info(f"📄 Récupération du rapport {report_id}")
            report = stripe.identity.VerificationReport.retrieve(report_id)
            document = report.get("document", {})

            profile.verified_first_name = document.get("first_name") or ""
            profile.verified_last_name = document.get("last_name") or ""

            logger.info(
                f"✅ Nom vérifié pour user_id={user_id} : "
                f"{profile.verified_first_name} {profile.verified_last_name}"
            )
        else:
            logger.warning(f"⚠️ Aucun rapport trouvé dans session pour user_id={user_id}")

    except Exception as e:
        logger.error(f"⚠️ Erreur récupération rapport Stripe Identity : {e}", exc_info=True)

    try:
        profile.save()
        logger.info(f"💾 Profil mis à jour pour user_id={user_id}")
    except Exception as e:
        logger.error(f"❌ Impossible de sauvegarder le profil user_id={user_id} : {e}", exc_info=True)


def _handle_identity_failure(session, reason="unknown"):
    logger.info(f"🔔 [Stripe Identity] Échec de vérification (raison={reason})")

    user_id = session.get("metadata", {}).get("user_id")
    if not user_id:
        logger.error("❌ user_id manquant dans metadata Stripe Identity")
        return

    try:
        User = get_user_model()
        user = User.objects.get(id=user_id)
        profile = Profile.objects.get(user=user)
    except Exception as e:
        logger.error(f"❌ Impossible de récupérer User/Profile pour user_id={user_id} : {e}")
        return

    profile.ci_is_verified = False
    profile.verified_first_name = ""
    profile.verified_last_name = ""

    try:
        profile.save()
        logger.warning(f"⚠️ Profil marqué comme non vérifié pour user_id={user_id}")
    except Exception as e:
        logger.error(f"❌ Impossible de sauvegarder le profil user_id={user_id} : {e}", exc_info=True)
