document.addEventListener("DOMContentLoaded", function () {
    // Sélectionne tous les carrousels
    const carousels = document.querySelectorAll(".carousel-container");
    const DEFAULT_AUTOPLAY_DELAY = 4000;

    carousels.forEach((carouselContainer) => {
        let slideIndex = 0;
        let autoplayTimer = null;
        // Délai personnalisable par carrousel : data-autoplay="7000"
        const autoplayDelay = parseInt(carouselContainer.dataset.autoplay, 10) || DEFAULT_AUTOPLAY_DELAY;
        const slides = carouselContainer.querySelectorAll(".mySlides");
        const carousel = carouselContainer.querySelector(".carousel");
        const prevBtn = carouselContainer.querySelector(".prev");
        const nextBtn = carouselContainer.querySelector(".next");
        // Les points peuvent être dans le carrousel (overlay sur l'image) ou juste à côté
        const dotsScope = carouselContainer.querySelector(".carousel-dots")
            ? carouselContainer
            : carouselContainer.parentElement;
        const dots = dotsScope.querySelectorAll(".carousel-dot");

        if (!carousel || slides.length === 0) return;

        function showDivs(n) {
            slideIndex = (n + slides.length) % slides.length;
            carousel.style.transform = `translateX(-${slideIndex * 100}%)`;

            dots.forEach((dot, i) => {
                dot.style.opacity = i === slideIndex ? "1" : "0.5";
                dot.style.transform = i === slideIndex ? "scale(1.15)" : "scale(1)";
            });
        }

        function plusDivs(n) {
            showDivs(slideIndex + n);
        }

        function startAutoplay() {
            if (slides.length <= 1) return;
            // Toujours repartir d'un timer propre : survol et focus peuvent se chevaucher
            clearInterval(autoplayTimer);
            autoplayTimer = setInterval(() => plusDivs(1), autoplayDelay);
        }

        function stopAutoplay() {
            clearInterval(autoplayTimer);
        }

        function restartAutoplay() {
            stopAutoplay();
            startAutoplay();
        }

        // Laisse le temps de lire : on suspend au survol et au focus clavier
        carouselContainer.addEventListener("mouseenter", stopAutoplay);
        carouselContainer.addEventListener("mouseleave", startAutoplay);
        carouselContainer.addEventListener("focusin", stopAutoplay);
        carouselContainer.addEventListener("focusout", startAutoplay);

        // Associe les boutons aux bons carrousels (s'ils existent)
        if (prevBtn) prevBtn.addEventListener("click", () => { plusDivs(-1); restartAutoplay(); });
        if (nextBtn) nextBtn.addEventListener("click", () => { plusDivs(1); restartAutoplay(); });

        dots.forEach((dot, i) => {
            dot.addEventListener("click", () => { showDivs(i); restartAutoplay(); });
        });

        showDivs(slideIndex);
        startAutoplay();
    });
});