var EYE_OPEN = '<path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>';
var EYE_OFF  = '<path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88L6.59 6.59m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>';

function togglePassword(inputId, btn) {
  var input = document.getElementById(inputId);
  if (!input) return;
  var isHidden = input.type === 'password';
  input.type = isHidden ? 'text' : 'password';
  btn.querySelector('svg').innerHTML = isHidden ? EYE_OFF : EYE_OPEN;
  btn.setAttribute('aria-label', isHidden ? 'Masquer le mot de passe' : 'Afficher le mot de passe');
}

(function () {
  const input = document.getElementById('password');
  const bar = document.getElementById('password-strength-bar');
  const fill = document.getElementById('password-strength-fill');
  const label = document.getElementById('password-strength-label');
  const submitBtn = document.getElementById('signup-submit');

  // --- Indicateur de force ---
  if (input && bar && fill && label) {
    input.addEventListener('input', function () {
      const val = this.value;

      if (!val) {
        bar.classList.add('hidden');
        label.classList.add('hidden');
        return;
      }

      bar.classList.remove('hidden');
      label.classList.remove('hidden');

      let score = 0;
      if (val.length >= 12) score++;
      if (val.length >= 16) score++;
      if (/[A-Z]/.test(val)) score++;
      if (/[^a-zA-Z0-9]/.test(val)) score++;
      if (!/^\d+$/.test(val)) score++;

      const levels = [
        { min: 0, max: 1, width: '25%', color: '#ef4444', text: 'Faible' },
        { min: 2, max: 2, width: '50%', color: '#f97316', text: 'Moyen' },
        { min: 3, max: 3, width: '75%', color: '#eab308', text: 'Bien' },
        { min: 4, max: 5, width: '100%', color: '#22c55e', text: 'Fort' },
      ];

      const level = levels.find(l => score >= l.min && score <= l.max) || levels[0];
      fill.style.width = level.width;
      fill.style.backgroundColor = level.color;
      label.textContent = level.text;
      label.style.color = level.color;
    });
  }

  // --- Protection double-clic ---
  if (submitBtn) {
    submitBtn.closest('form').addEventListener('submit', function () {
      submitBtn.disabled = true;
      submitBtn.textContent = submitBtn.dataset.loading || 'Inscription en cours…';
    });
  }
})();
