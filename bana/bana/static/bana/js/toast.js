// Toasts overlay — auto-dismiss + close bouton
(function () {
  function initToasts(root = document) {
    const toasts = root.querySelectorAll('[data-toast]');
    toasts.forEach((toast) => {
      const ms = parseInt(toast.getAttribute('data-toast-timeout') || '4600', 10);
      toast.style.setProperty('--toast-timeout', (ms / 1000) + 's');

      const hide = () => {
        toast.classList.add('animate-toast-leave');
        setTimeout(() => toast.remove(), 220);
      };
      const timer = setTimeout(hide, ms);

      const btn = toast.querySelector('[data-toast-close]');
      if (btn) btn.addEventListener('click', () => { clearTimeout(timer); hide(); });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initToasts());
  } else {
    initToasts();
  }

  document.addEventListener('htmx:afterSwap', (e) => initToasts(e.target));
})();