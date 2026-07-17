(function () {
    var STORAGE_KEY = 'bana_cookie_consent';
    var banner = document.getElementById('cookie-banner');
    if (!banner) return;

    // Déjà choisi → on n'affiche rien
    if (localStorage.getItem(STORAGE_KEY)) return;

    function saveChoice(accepted) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({
            essential: true,
            analytics: accepted,
            timestamp: Date.now()
        }));
    }

    function dismiss(accepted) {
        saveChoice(accepted);
        banner.classList.remove('cookie-banner--entering');
        banner.classList.add('cookie-banner--hidden');
        setTimeout(function () { banner.hidden = true; }, 450);
    }

    // Affichage avec un court délai pour ne pas bloquer le premier rendu
    setTimeout(function () {
        banner.hidden = false;
        banner.classList.add('cookie-banner--entering');
    }, 500);

    var btnAccept = document.getElementById('cookie-accept');
    var btnRefuse = document.getElementById('cookie-refuse');
    if (btnAccept) btnAccept.addEventListener('click', function () { dismiss(true); });
    if (btnRefuse) btnRefuse.addEventListener('click', function () { dismiss(false); });
})();
