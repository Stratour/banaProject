from monapp.models import Languages  # Remplacez 'monapp' par le nom de votre application

# Liste des langues et de leurs abréviations (ISO 639-1 ou 639-2)
langues_data = [
    {'name': 'Albanais', 'abbr': 'sq'},
    {'name': 'Allemand', 'abbr': 'de'},
    {'name': 'Anglais', 'abbr': 'en'},
    {'name': 'Arabe', 'abbr': 'ar'},
    {'name': 'Basque', 'abbr': 'eu'},
    {'name': 'Berbère', 'abbr': 'ber'},
    {'name': 'Bosnien', 'abbr': 'bs'},
    {'name': 'Cantonais', 'abbr': 'yue'},
    {'name': 'Catalan', 'abbr': 'ca'},
    {'name': 'Croate', 'abbr': 'hr'},
    {'name': 'Danois', 'abbr': 'da'},
    {'name': 'Dari', 'abbr': 'prs'},
    {'name': 'Espagnol', 'abbr': 'es'},
    {'name': 'Estonien', 'abbr': 'et'},
    {'name': 'Finnois', 'abbr': 'fi'},
    {'name': 'Français', 'abbr': 'fr'},
    {'name': 'Gaélique', 'abbr': 'gla'},
    {'name': 'Grec', 'abbr': 'el'},
    {'name': 'Hassanya', 'abbr': 'mya'},
    {'name': 'Hébreu', 'abbr': 'he'},
    {'name': 'Hindi', 'abbr': 'hi'},
    {'name': 'Hongrois', 'abbr': 'hu'},
    {'name': 'Italien', 'abbr': 'it'},
    {'name': 'KINYARWANDA', 'abbr': 'rw'},
    {'name': 'Kurde', 'abbr': 'ku'},
    {'name': 'Letton', 'abbr': 'lv'},
    {'name': 'Lingala', 'abbr': 'ln'},
    {'name': 'Lituanien', 'abbr': 'lt'},
    {'name': 'Malgache', 'abbr': 'mg'},
    {'name': 'Malinké', 'abbr': 'mnk'},
    {'name': 'Mandarin', 'abbr': 'zh'},
    {'name': 'Néerlandais', 'abbr': 'nl'},
    {'name': 'Norvégien', 'abbr': 'no'},
    {'name': 'Ourdou', 'abbr': 'ur'},
    {'name': 'Pachto', 'abbr': 'ps'},
    {'name': 'Polonais', 'abbr': 'pl'},
    {'name': 'Portugais', 'abbr': 'pt'},
    {'name': 'Roumain', 'abbr': 'ro'},
    {'name': 'Russe', 'abbr': 'ru'},
    {'name': 'Serbe', 'abbr': 'sr'},
    {'name': 'Slovaque', 'abbr': 'sk'},
    {'name': 'Slovène', 'abbr': 'sl'},
    {'name': 'Somali', 'abbr': 'so'},
    {'name': 'Suédois', 'abbr': 'sv'},
    {'name': 'Swahili', 'abbr': 'sw'},
    {'name': 'Tamoul', 'abbr': 'ta'},
    {'name': 'Tchèque', 'abbr': 'cs'},
    {'name': 'Thaï', 'abbr': 'th'},
    {'name': 'Turc', 'abbr': 'tr'},
    {'name': 'Vietnamien', 'abbr': 'vi'},
    {'name': 'Wolof', 'abbr': 'wo'},
    {'name': 'Autre', 'abbr': 'zz'} # 'zz' est un code générique pour 'autre'
]

# Création des objets Languages à partir de la liste
langues_a_creer = [
    Languages(lang_name=lang['name'], lang_abbr=lang['abbr'])
    for lang in langues_data
]

# Insertion des objets dans la base de données
Languages.objects.bulk_create(langues_a_creer, ignore_conflicts=True)

print(f"Insertion de {len(langues_a_creer)} langues terminée.")
