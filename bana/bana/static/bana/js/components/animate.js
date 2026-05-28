document.addEventListener("DOMContentLoaded", () => {

  const elements = document.querySelectorAll(".animate-on-scroll");

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {

        const el = entry.target;

        // delay automatique si dans un groupe
        const delay = el.dataset.delay || 0;

        setTimeout(() => {
          el.classList.add("is-visible");
        }, delay);

        observer.unobserve(el);
      }
    });
  }, {
    threshold: 0.15
  });

  elements.forEach(el => observer.observe(el));

});

window.addEventListener("scroll", () => {
  const parallax = document.querySelectorAll(".parallax");

  parallax.forEach(el => {
    const speed = el.dataset.speed || 0.2;
    const y = window.scrollY * speed;
    el.style.transform = `translateY(${y}px)`;
  });
});