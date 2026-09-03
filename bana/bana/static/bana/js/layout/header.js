/* ===== Éléments DOM ===== */
const menuToggle = document.getElementById('menu-toggle');
const mobileMenu = document.getElementById('mobile-menu');
const overlay    = document.getElementById('mobile-overlay');
const iconOpen   = document.getElementById('icon-open');
const iconClose  = document.getElementById('icon-close');

/* ===== Ouverture du menu mobile ===== */
function openMenu() {
  mobileMenu.classList.remove('opacity-0', '-translate-y-2', 'pointer-events-none');
  mobileMenu.classList.add('opacity-100', 'translate-y-0', 'pointer-events-auto');
  overlay.classList.remove('opacity-0', 'pointer-events-none');
  overlay.classList.add('opacity-100');
  iconOpen.style.opacity = '0';
  iconOpen.style.transform = 'rotate(-90deg) scale(0.75)';
  iconClose.style.opacity = '1';
  iconClose.style.transform = 'rotate(0deg) scale(1)';
  if (typeof closeAppAvatarMobile === 'function') closeAppAvatarMobile();
  document.body.classList.add('overflow-hidden');
}

/* ===== Fermeture du menu mobile ===== */
function closeMenu() {
  mobileMenu.classList.add('opacity-0', '-translate-y-2', 'pointer-events-none');
  mobileMenu.classList.remove('opacity-100', 'translate-y-0', 'pointer-events-auto');
  overlay.classList.add('opacity-0', 'pointer-events-none');
  overlay.classList.remove('opacity-100');
  iconOpen.style.opacity = '1';
  iconOpen.style.transform = 'rotate(0deg) scale(1)';
  iconClose.style.opacity = '0';
  iconClose.style.transform = 'rotate(90deg) scale(0.75)';
  document.body.classList.remove('overflow-hidden');
}

/* ===== Événements ===== */
menuToggle.addEventListener('click', () => {
  mobileMenu.classList.contains('opacity-0') ? openMenu() : closeMenu();
});

overlay.addEventListener('click', closeMenu);

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeMenu();
});

/* ===== Shadow au scroll ===== */
window.addEventListener('scroll', () => {
  document.getElementById('site-header')
    .classList.toggle('shadow-md', window.scrollY > 10);
}, { passive: true });

/* ===== Hauteur du header exposée en variable CSS =====
   Le header vitrine est "sticky top-0" et la sidebar app l'est aussi (voir
   base.html) : sans ça, les deux se disputent la même position en haut de
   l'écran au scroll et le header cache le sommet de la sidebar. On mesure la
   hauteur réelle du header (elle varie selon le breakpoint) et on l'expose en
   variable CSS pour que la sidebar se cale juste en dessous. */
const siteHeaderEl = document.getElementById('site-header');
function syncHeaderHeightVar() {
  if (siteHeaderEl) {
    document.documentElement.style.setProperty('--app-header-h', `${siteHeaderEl.offsetHeight}px`);
  }
}
syncHeaderHeightVar();
window.addEventListener('resize', syncHeaderHeightVar);
if (siteHeaderEl && window.ResizeObserver) {
  new ResizeObserver(syncHeaderHeightVar).observe(siteHeaderEl);
}
