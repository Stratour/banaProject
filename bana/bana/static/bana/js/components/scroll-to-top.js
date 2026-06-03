(function () {
  const btn = document.getElementById('scroll-to-top-btn');
  if (!btn) return;
  window.addEventListener('scroll', function () {
    const show = window.scrollY > 300;
    btn.classList.toggle('opacity-0', !show);
    btn.classList.toggle('pointer-events-none', !show);
    btn.classList.toggle('opacity-100', show);
  }, { passive: true });
})();
