from django.shortcuts import render

# --- Home page ---------------------------------------------------------------------------
def home(request):
    home_benefits = [
        {'img_src': 'bana/img/icon/Icon_clock.svg', 'title': 'Time saving', 'highlight': 'Flexibility', 'description': 'in your calendar'},
        {'img_src': 'bana/img/icon/Icon_currency.svg', 'title': 'Economic', 'highlight': 'money', 'description': 'Save on gasoline'},
        {'img_src': 'bana/img/icon/Icon_earth.svg', 'title': 'Ecological', 'highlight': 'alternative', 'description': 'Using alternative transport'},
        {'img_src': 'bana/img/icon/Icon_hearth.svg', 'title': 'Community', 'highlight': 'Social connection', 'description': 'Sharing moments'}
    ]
    
    home_roles = [
        {'img_src': 'bana/img/other/Bana_Parent.png', 'alt_text': 'Parent Icon', 'link_text': 'I am a parent', 'link_url': '#'},
        {'img_src': 'bana/img/other/Bana_Mentor.png', 'alt_text': 'Mentor Icon', 'link_text': 'I am a mentor', 'link_url': '#'},
        {'img_src': 'bana/img/other/Bana_Community.png', 'alt_text': 'Community Icon', 'link_text': 'I am a community member', 'link_url': '#'}
    ]
    return render(request, 'home.html', {"home_benefits": home_benefits, "home_roles": home_roles})

# --- Conact page ---------------------------------------------------------------------------
def contact(request):
    return render(request, 'contact.html')

# --- About page ---------------------------------------------------------------------------
def about(request):
    return render(request, 'about.html')

# --- Work page ---------------------------------------------------------------------------
def work(request):
    work_steps = [
        {'img_src': 'bana/img/icon/Icon_profile.svg', 'title': '1. Create your profile', 'highlight': 'community of parents', 'description': 'Join a community of parents from your child’s school or activities.'},
        {'img_src': 'bana/img/icon/Icon_place.svg', 'title': '2. Indicate your routes', 'highlight': 'Bana connects you', 'description': 'Share trip requests or respond to alerts, and Bana connects you.'},
        {'img_src': 'bana/img/icon/Icon_message.svg', 'title': '3. Compose your tribe', 'highlight': 'build your trusted tribe', 'description': 'Find parents with similar routes, choose profiles, and build your trusted tribe.'}
    ]
    
    work_roles = [
        {'img_src': 'bana/img/other/Bana_Parent.png', 'alt_text': 'Parent Icon', 'link_text': 'I am a parent', 'link_url': '#'},
        {'img_src': 'bana/img/other/Bana_Mentor.png', 'alt_text': 'Mentor Icon', 'link_text': 'I am a mentor', 'link_url': '#'},
        {'img_src': 'bana/img/other/Bana_Community.png', 'alt_text': 'Community Icon', 'link_text': 'I am a community member', 'link_url': '#'}
    ]
    
    work_profiles = [
        {
            'img_src': 'bana/img/other/Nyota.png',
            'name': 'Nyota Delecourt',
            'short_bio': 'Mother of two (2010, 2023) with a marketing background and experience in HR, purchasing, and project management.',
            'full_description': 'Passionate about family well-being. I juggle life as a mom to a teenager and a baby, balancing basketball practices, bottles, and meetings. I value sustainable living and dream of a world where parenting is easier and children grow up peacefully.'
        },
        {
            'img_src': 'bana/img/other/Bernard.png',
            'name': 'Bernard Lambeau',
            'short_bio': 'Father of 3 children, IT profile, experience in platform development for mobility. Committed and sensitive to the environment.',
            'full_description': 'I aim to know everything about mobility in Belgium, or, perhaps more realistically, to contribute to its improvement. I am particularly interested in mobility in rural areas.'
        }
    ]
    return render(request, 'work.html', {"work_steps": work_steps, "work_roles": work_roles, "work_profiles": work_profiles})


# --- Parent page ---------------------------------------------------------------------------
def parent(request):
    features_search = [
        {"icon": "Icon_clock.svg", "title": "Time saving", "highlight": "Flexibility", "text": "in your calendar"},
        {"icon": "Icon_currency.svg", "title": "Economic", "highlight": "money", "text": "on gasoline"},
        {"icon": "Icon_earth.svg", "title": "Ecological", "highlight": "alternative", "text": "transport"},
        {"icon": "Icon_hearth.svg", "title": "Community", "highlight": "Social connection", "text": "& sharing moments"},
    ]

    features_share = [
        {"icon": "Icon_flexibility.svg", "title": "Flexibility", "highlight": "You choose", "text": "the rides you share"},
        {"icon": "Icon_experience.svg", "title": "Experience", "highlight": "development", "text": "Support children's"},
        {"icon": "Icon_support.svg", "title": "Most importantly", "highlight": "in your community", "text": "Support other parents"},
        {"icon": "Icon_trust.svg", "title": "Trust", "highlight": "Provide safe", "text": ", reliable rides with trusted parents."},
    ]
    return render(request, 'parent.html', {"features_search": features_search, "features_share": features_share})

