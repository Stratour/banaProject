document.querySelectorAll('.faq-item').forEach(details => {
  const summary = details.querySelector('summary');
  const body = details.querySelector('.faq-body');

  summary.addEventListener('click', e => {
    e.preventDefault();

    if (details.open) {
      body.style.transition = 'grid-template-rows 0.22s ease-in';
      body.style.gridTemplateRows = '0fr';
      const onClose = ev => {
        if (ev.propertyName !== 'grid-template-rows') return;
        body.removeEventListener('transitionend', onClose);
        details.removeAttribute('open');
        body.style.transition = '';
      };
      body.addEventListener('transitionend', onClose);
    } else {
      details.setAttribute('open', '');
      requestAnimationFrame(() => {
        body.style.transition = '';
        body.style.gridTemplateRows = '1fr';
      });
    }
  });
});
