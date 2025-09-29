document.addEventListener("DOMContentLoaded", function () {
    // Sélectionne tous les carrousels
    const carousels = document.querySelectorAll(".carousel-container");

    carousels.forEach((carouselContainer) => {
        let slideIndex = 0;
        const slides = carouselContainer.querySelectorAll(".mySlides");
        const carousel = carouselContainer.querySelector(".carousel");

        function showDivs(n) {
            slideIndex = (n + slides.length) % slides.length;
            carousel.style.transform = `translateX(-${slideIndex * 100}%)`;
        }

        function plusDivs(n) {
            showDivs(slideIndex + n);
        }

        // Associe les boutons aux bons carrousels
        carouselContainer.querySelector(".prev").addEventListener("click", () => plusDivs(-1));
        carouselContainer.querySelector(".next").addEventListener("click", () => plusDivs(1));

        showDivs(slideIndex);
    });
});