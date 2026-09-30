repo: Stratour/banaProject
branch: main

## Last sync
date: 2026-09-22T14:02:23Z

### Updated in this project
- Lu les 42 templates email existants (`account/email/*.txt`, `trajects/email/*.txt`) — tous en texte brut, envoyés par `send_mail`.
- Repris la charte du repo : `#007F73`, dégradé `#0F5F4B → #0ab092`, lime `#D7FC19` (tailwind.config.js).
- Copié le logo `bana/bana/static/bana/img/shared/bana_logo.png` pour les maquettes.
- Créé « Emails Bana.dc.html » : 8 maquettes email HTML (tables + styles inline).

## Screen map
| Maquette | Source repo |
|---|---|
| 01 Confirmation d'inscription | bana/accounts/templates/account/email/email_confirmation_message.txt |
| 02 Réinitialisation mot de passe | bana/accounts/templates/account/email/password_reset_key_message.txt |
| 03 Changement d'adresse email | bana/accounts/templates/account/email/email_change_confirmation_message.txt, bana/accounts/utils.py |
| 04 Nouvelle demande de réservation | bana/trajects/templates/trajects/email/new_reservation_request_message.txt |
| 05 Réservation confirmée | bana/trajects/templates/trajects/email/reservation_confirmed_message.txt |
| 06 Réservation refusée | bana/trajects/templates/trajects/email/reservation_rejected_message.txt |
| 07 Accompagnateur trouvé | bana/trajects/templates/trajects/email/help_proposed_bulk_message.txt |
| 08 Notification de sécurité | bana/accounts/templates/account/email/base_notification.txt |
| Charte (couleurs, logo) | bana/theme/static_src/tailwind.config.js, bana/bana/templates/layouts/base.html |
