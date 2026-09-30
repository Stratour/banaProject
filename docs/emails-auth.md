# Emails d'authentification — référence pour le design

Document de référence pour la mise en forme des emails de compte : inscription, mot de passe,
adresse e-mail. Il liste ce que Bana envoie, qui le reçoit, ce qui le déclenche, et **les
variables disponibles dans chaque gabarit**.

Pendant de `emails-trajects.md`, qui couvre les emails de trajets et de réservations.

- Code d'envoi : **django-allauth** (`DefaultAccountAdapter.send_mail`) — aucun adaptateur
  personnalisé dans le projet. Seule exception : le changement d'adresse, envoyé par
  `bana/accounts/utils.py` (voir §6).
- Gabarits : `bana/accounts/templates/account/email/` — une paire `*_subject.txt` /
  `*_message.txt` par email, toutes héritant du squelette `base_message.txt`.
- Les gabarits sont en **texte brut**. Une version HTML devra consommer les mêmes variables.
- Expéditeur : `Bana <contact@bana.mobi>` (`DEFAULT_FROM_EMAIL`) pour tous.
- **Pas de préfixe d'objet** : `ACCOUNT_EMAIL_SUBJECT_PREFIX = ''`, les objets partent tels
  quels, sans `[bana.mobi]` devant.

---

## Forme commune

Tous ces emails suivent la même trame, posée par `base_message.txt` :

```
Bonjour <prénom>,

<ce qui vient de se passer>

<le lien, seul sur sa ligne>

<phrase pour qui n'est pas à l'origine de la demande>

L'équipe Bana
```

C'est la trame des emails de trajets. Deux différences avec eux : la signature « L'équipe
Bana » (les emails de trajets n'en ont pas) et l'absence de bloc récapitulatif — il n'y a rien
à récapituler, l'action tient dans le lien.

### Variables communes

| Variable | Type | Exemple | Toujours présente ? |
|---|---|---|---|
| `user` | User | — | **Non** — absent de §4 et §5 (voir ci-dessous) |
| `email` | str | `"marie@example.com"` | Oui — l'adresse **destinataire** |
| `current_site` | objet | `.name` = `.domain` = `"www.bana.mobi"` | Oui — ⚠️ voir l'encadré |
| `request` | HttpRequest | — | Oui |

> **⚠️ `current_site.name` n'est pas un nom de marque.** `django.contrib.sites` n'est pas
> installé : Django retombe sur `RequestSite`, où `name` et `domain` valent tous deux le
> **host HTTP** (`www.bana.mobi`). Écrire « L'équipe de {{ current_site.name }} » affiche donc
> « L'équipe de www.bana.mobi ». Le nom « Bana » est écrit en dur dans les gabarits.

### Le prénom du destinataire

Calculé dans `base_message.txt`, dans cet ordre :

1. `user.profile.verified_first_name` — identité vérifiée par Stripe Identity ;
2. `user.first_name` — prénom saisi à l'inscription ;
3. rien → **« Bonjour, »** tout court.

Jamais l'adresse email en repli : elle n'apprend rien au destinataire, qui la lit déjà dans
l'en-tête. Le design doit prévoir la salutation **sans nom** — elle se produit sur les emails
§4 et §5, qui n'ont aucun `user` en contexte, et sur tout compte sans prénom renseigné.

---

## 1. `email_confirmation_signup` — confirmation d'inscription

| | |
|---|---|
| **Pour** | le **nouveau membre**, à l'adresse qu'il vient de saisir |
| **Déclencheur** | création de compte |
| **Criticité** | **bloquante** — `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'` : sans ce clic, le compte ne sert à rien |

| Variable | Type | Exemple |
|---|---|---|
| `activate_url` | str | `"https://www.bana.mobi/fr/accounts/confirm-email/MjE:1uK2a:9f…/"` |
| `key` | str | la clé seule, si on préfère composer le lien soi-même |

```
Objet : Bienvenue sur Bana : confirmez votre adresse e-mail

Bonjour Amina,

Merci pour votre inscription sur Bana !

Il reste une étape : confirmez cette adresse e-mail pour activer votre compte.

https://www.bana.mobi/fr/accounts/confirm-email/MjE:1uK2a:9f…/

Si vous n'êtes pas à l'origine de cette inscription, ignorez simplement cet e-mail.

L'équipe Bana
```

C'est **le premier email qu'un membre reçoit de Bana** : c'est lui qui pose le ton de la
marque. Un seul lien, une seule action — ne rien y ajouter qui détourne du clic.

Le lien vaut **3 jours** (`ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS`), mais allauth ne met pas
ce nombre en contexte : le texte actuel ne l'annonce pas. Pour l'afficher, il faudra un
adaptateur `ACCOUNT_ADAPTER` qui l'injecte.

---

## 2. `email_confirmation` — adresse ajoutée à un compte existant

| | |
|---|---|
| **Pour** | le **membre**, à la nouvelle adresse |
| **Déclencheur** | ajout d'une adresse sur un compte déjà actif |
| **Criticité** | courante |

Mêmes variables que §1. Gabarit **distinct** de §1 : les deux partageaient le même texte, qui
souhaitait donc la bienvenue à quelqu'un déjà inscrit.

```
Objet : Confirmez votre adresse e-mail

Cette adresse e-mail vient d'être ajoutée à votre compte Bana. Confirmez-la pour pouvoir
l'utiliser :
```

---

## 3. `password_reset_key` — lien de réinitialisation

| | |
|---|---|
| **Pour** | le **membre** |
| **Déclencheur** | formulaire « mot de passe oublié » |
| **Criticité** | **bloquante** — seule voie de retour pour un membre qui ne peut plus se connecter |

| Variable | Type | Exemple |
|---|---|---|
| `password_reset_url` | str | `"https://www.bana.mobi/fr/accounts/password/reset/key/MjE-cgj9x8-3f1a…/"` |
| `uid`, `key` | str | composants du lien, si besoin de le recomposer |

```
Objet : Réinitialisez votre mot de passe Bana

Vous avez demandé à réinitialiser le mot de passe de votre compte Bana.

Choisissez un nouveau mot de passe depuis le lien ci-dessous :

https://www.bana.mobi/fr/accounts/password/reset/key/MjE-set-password/

Si vous n'êtes pas à l'origine de cette demande, ignorez cet e-mail : votre mot de passe
actuel reste valable.
```

> `username` **n'existe pas** dans ce contexte : allauth ne le fournit que si la connexion par
> nom d'utilisateur est active, or `ACCOUNT_LOGIN_METHODS = {'email'}`. Ne pas prévoir de
> rappel d'identifiant — l'identifiant, c'est l'adresse email.

Validité du lien : `PASSWORD_RESET_TIMEOUT` n'est pas surchargé, donc **3 jours** (défaut
Django). Non exposé en contexte non plus.

---

## 4. `unknown_account` — réinitialisation pour une adresse inconnue

| | |
|---|---|
| **Pour** | la personne qui a saisi l'adresse |
| **Déclencheur** | « mot de passe oublié » sur une adresse sans compte |
| **Particularité** | **pas de `user` en contexte** → « Bonjour, » |

| Variable | Type | Exemple |
|---|---|---|
| `email` | str | `"inconnu@example.com"` |
| `signup_url` | str | `"https://www.bana.mobi/fr/accounts/signup/"` |

Cet email existe parce que `ACCOUNT_PREVENT_ENUMERATION = True` : le formulaire répond la même
chose que l'adresse existe ou non, pour ne pas révéler qui est membre. **C'est l'email qui fait
la distinction** — d'où deux conséquences pour le design :

- il est reçu par quelqu'un qui **n'est pas** membre : pas de « votre compte », pas de ton
  familier ;
- il doit rester sobre. Une grosse bannière « Rejoignez Bana ! » transformerait un mécanisme de
  sécurité en prospection.

```
Objet : Aucun compte Bana avec cette adresse

Vous avez demandé à réinitialiser le mot de passe du compte associé à inconnu@example.com,
mais aucun compte Bana n'utilise cette adresse.
```

---

## 5. `account_already_exists` — inscription sur une adresse déjà prise

| | |
|---|---|
| **Pour** | le **membre existant** |
| **Déclencheur** | tentative de création de compte avec une adresse déjà enregistrée |
| **Particularité** | **pas de `user` en contexte** → « Bonjour, » |

| Variable | Type | Exemple |
|---|---|---|
| `email` | str | `"deja@example.com"` |
| `password_reset_url` | str | lien de réinitialisation |
| `signup_url` | str | présent mais inutilisé — proposer de s'inscrire n'aurait pas de sens ici |

Même logique anti-énumération que §4. Le cas courant est un membre qui a oublié qu'il avait un
compte : le CTA est donc la **réinitialisation**, pas l'inscription.

---

## 6. `email_change_confirmation` — changement d'adresse

| | |
|---|---|
| **Pour** | le **membre**, à la **nouvelle** adresse |
| **Déclencheur** | `accounts.utils.send_change_email_confirmation`, depuis l'espace compte |
| **Particularité** | **envoyé hors allauth** — voir l'encadré |

| Variable | Type | Exemple | Note |
|---|---|---|---|
| `user` | User | — | présent |
| `activate_url` | str | `"https://www.bana.mobi/fr/email/change/confirm/<clé>/"` | route maison `accounts:email_change_confirm` |
| `expiration_days` | int | `3` | **seul email à exposer la durée de validité** |
| `current_site` | dict | `{"name": host, "domain": host}` | un dict, pas un objet `Site` |

```
Objet : Confirmez votre nouvelle adresse e-mail

Vous avez demandé à utiliser cette adresse e-mail pour votre compte Bana.

Confirmez ce changement depuis le lien ci-dessous, valable 3 jour(s) :

https://www.bana.mobi/fr/email/change/confirm/<clé>/

Tant que ce lien n'est pas ouvert, votre ancienne adresse reste celle de connexion. Une fois
le changement confirmé, elle est remplacée par celle-ci.
```

Le sort de l'ancienne adresse est dit explicitement parce qu'il est irréversible : à la
confirmation, le signal `email_confirmed` (`accounts/signals.py`) **supprime** les autres
`EmailAddress` du compte. allauth authentifie sur n'importe quelle adresse liée, sans regarder
`primary` ni `verified` : une ancienne adresse laissée en base permettrait encore de se
connecter. Après confirmation, l'ancienne adresse ne fonctionne donc plus — une surprise s'il
fallait la découvrir à la prochaine connexion.

> **⚠️ Cet email n'aura pas de version HTML « gratuitement ».** Il part par
> `django.core.mail.send_mail(...)` sans argument `html_message` : ajouter un
> `email_change_confirmation_message.html` ne suffira pas, il faudra modifier
> `accounts/utils.py`. Tous les autres emails de ce document, eux, sont envoyés par allauth —
> voir « Passer en HTML » plus bas.

---

## 7. Emails de notification — écrits mais **jamais envoyés**

Six gabarits existent, héritant de `base_notification.txt` : `password_changed`, `password_set`,
`email_changed`, `email_deleted`, `email_confirm`, `password_reset`.

**Aucun ne part aujourd'hui** : `ACCOUNT_EMAIL_NOTIFICATIONS` n'est pas défini dans
`settings.py` et son défaut allauth est `False`. Les activer est une ligne de réglage.

Ils ajoutent au corps un bloc de contexte de sécurité :

| Variable | Type | Exemple |
|---|---|---|
| `ip` | str | `"81.2.3.4"` |
| `user_agent` | str | `"Mozilla/5.0 …"` (tronqué par allauth) |
| `timestamp` | datetime | — |
| `from_email` / `to_email` | str | `email_changed` uniquement |
| `deleted_email` | str | `email_deleted` uniquement |

Si le design les couvre, prévoir un bloc « provenance » distinct du corps du message : adresse
IP, navigateur, date. Le `user_agent` est une chaîne brute, longue et laide — à traiter comme
une donnée technique, pas comme du texte.

---

## 8. Hors périmètre

- `password_reset_code`, `login_code` — flux par **code à 6 chiffres** au lieu d'un lien. Non
  activés (`ACCOUNT_LOGIN_BY_CODE_ENABLED` et la vérification par code sont absents des
  réglages). Les gabarits existent côté allauth ; ils ne partent pas.
- `socialaccount/email/account_connected_message.txt` et `account_disconnected_message.txt` —
  connexion Google. Le provider est **commenté** dans `settings.py`.

---

## Cas de figure à prévoir dans le design

1. **Destinataire sans nom** — « Bonjour, » sans prénom : systématique sur §4 et §5, fréquent
   ailleurs (le prénom n'est pas obligatoire à l'inscription).
2. **Destinataire qui n'est pas membre** (§4) — aucun « votre compte », aucun contenu qui
   suppose une relation existante.
3. **Liens très longs** — les clés de confirmation et de réinitialisation font ~60 caractères.
   L'URL complète dépasse 90 caractères : elle doit rester **cliquable et visible**, jamais
   tronquée au point de ne plus être copiable à la main.
4. **Un seul CTA par email** — ce sont des emails d'action unique. Pas de liens secondaires qui
   concurrencent le bouton principal.
5. **Clients mail sans images ni CSS** — ces emails sont les seuls à pouvoir bloquer un
   membre. La version texte doit rester parfaitement utilisable seule.

---

## Pied de page (à ajouter, non implémenté)

Même constat que pour les emails de trajets : aucun pied de page aujourd'hui. Minimum légal
belge et RGPD à prévoir dans le design :

- Dénomination sociale, adresse du siège, **numéro d'entreprise BCE**
- `contact@bana.mobi` · `+32 495 283 791`
- Raison de l'envoi
- Liens CGU · Confidentialité · Mentions légales

> Sur les emails d'authentification, **pas de lien de désinscription** : ce sont des emails
> transactionnels indispensables au compte, ils ne relèvent pas du consentement marketing.

---

## Notes techniques

### Passer en HTML

Pour les emails envoyés par allauth (§1 à §5, et §7), il suffit d'ajouter un fichier
`<nom>_message.html` **à côté** du `.txt` dans `accounts/templates/account/email/` :
`render_mail` le détecte, l'attache en alternative HTML et garde le `.txt` comme corps texte.
Aucun code à modifier. Les deux versions doivent rester synchronisées — le texte n'est pas un
repli négligeable, beaucoup de clients et de filtres ne lisent que lui.

Le changement d'adresse (§6) est la seule exception : voir son encadré.

### URLs

Construites par `request.build_absolute_uri` (allauth et `accounts/utils.py`), donc absolues et
sur le host de la requête. Les routes sont sous `i18n_patterns(prefix_default_language=True)` :
**toujours préfixées `/fr/`**.

### Confirmation en un clic

`ACCOUNT_CONFIRM_EMAIL_ON_GET = True` : ouvrir le lien confirme immédiatement, sans page
intermédiaire ni bouton à valider. Conséquence à connaître — un antivirus ou un filtre
anti-spam qui pré-visite les liens d'un message **consomme la confirmation** avant le
destinataire. Le lien reste donc à usage unique et le design ne doit pas le dupliquer
(bouton + URL en clair pointant tous deux vers la même clé, c'est déjà le cas de figure à
éviter le jour du passage en HTML : un seul élément cliquable).

### Traductions

Ces gabarits utilisent `{% trans %}` / `{% blocktrans %}`, contrairement à ceux des trajets qui
sont en français en dur. `LANGUAGES` ne déclare que `fr` pour l'instant : les chaînes
s'affichent telles qu'écrites. Les catalogues `en` et `nl` contiennent encore d'anciens msgids
devenus orphelins — un `makemessages` les nettoiera le jour où ces langues seront activées.
