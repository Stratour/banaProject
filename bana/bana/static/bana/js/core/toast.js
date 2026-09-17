// Toasts — fermeture automatique, barre de progression et bouton de fermeture.
//
// La barre est animée ici (Web Animations API) plutôt qu'en CSS : ce fichier et toast.css
// sont pré-cachés par le service worker, et une feuille de styles périmée laissait la barre
// figée à 100 %. Piloter la largeur en JS garde le minuteur et la barre sur la même horloge.
(function () {
  function initToasts(root = document) {
    root.querySelectorAll('[data-toast]').forEach((toast) => {
      if (toast.dataset.toastReady) return;   // évite un double init après un swap htmx
      toast.dataset.toastReady = '1';

      const ms = parseInt(toast.getAttribute('data-toast-timeout') || '5000', 10);

      const hide = () => {
        toast.classList.add('animate-toast-leave');
        setTimeout(() => toast.remove(), 220);
      };

      // Barre de progression : décroît sur toute la durée d'affichage.
      // Elle porte une information (temps restant) et n'est pas décorative : on la garde
      // même en prefers-reduced-motion, contrairement aux animations d'entrée et de sortie.
      const bar = toast.querySelector('[data-toast-progress]');
      let anim = null;
      if (bar && typeof bar.animate === 'function') {
        anim = bar.animate(
          [{ width: '100%' }, { width: '0%' }],
          { duration: ms, easing: 'linear', fill: 'forwards' }
        );
      }

      let timer = setTimeout(hide, ms);
      let startedAt = Date.now();
      let remaining = ms;

      // Au survol, le message reste lisible : minuteur et barre sont suspendus ensemble.
      toast.addEventListener('mouseenter', () => {
        clearTimeout(timer);
        remaining -= Date.now() - startedAt;
        if (anim) anim.pause();
      });
      toast.addEventListener('mouseleave', () => {
        startedAt = Date.now();
        timer = setTimeout(hide, Math.max(remaining, 600));
        if (anim) anim.play();
      });

      const btn = toast.querySelector('[data-toast-close]');
      if (btn) {
        btn.addEventListener('click', () => {
          clearTimeout(timer);
          if (anim) anim.cancel();
          hide();
        });
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initToasts());
  } else {
    initToasts();
  }

  document.addEventListener('htmx:afterSwap', (e) => initToasts(e.target));
})();
