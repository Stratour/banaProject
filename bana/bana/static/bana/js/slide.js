let currentIndex = 0;
const slider = document.getElementById('slider');

function updateSlider() {
    slider.style.transform = `translateX(-${currentIndex * 100}%)`;
}

function nextSlide() {
    const totalSlides = slider.children.length;
    currentIndex = (currentIndex + 1) % totalSlides;
    updateSlider();
}

function prevSlide() {
    const totalSlides = slider.children.length;
    currentIndex = (currentIndex - 1 + totalSlides) % totalSlides;
    updateSlider();
}