  (function () {
    const video = document.getElementById('video-element');
    const overlay = document.getElementById('play-overlay');

    overlay?.addEventListener('click', () => {
      overlay.classList.add('hidden');
      video.classList.remove('hidden');
      video.play?.();
    });
  })();