document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('faq-search');
    const chips = document.querySelectorAll('.faq-chip');
    const items = document.querySelectorAll('.faq-item');
    const categoryWraps = document.querySelectorAll('[data-category]');
    const frequentesHeading = document.getElementById('faq-frequentes-heading');
    const noResults = document.getElementById('faq-no-results');

    if (!searchInput || !items.length) return;

    let activeTheme = 'frequentes';

    function applyFilters() {
        const query = searchInput.value.trim().toLowerCase();
        let visibleCount = 0;

        items.forEach(item => {
            let matchesTheme;
            if (activeTheme === 'all') {
                matchesTheme = true;
            } else if (activeTheme === 'frequentes') {
                matchesTheme = item.dataset.featured === 'true';
            } else {
                matchesTheme = item.dataset.theme === activeTheme;
            }
            const matchesQuery = !query || item.textContent.toLowerCase().includes(query);
            const show = matchesTheme && matchesQuery;
            item.classList.toggle('hidden', !show);
            if (show) visibleCount++;
        });

        categoryWraps.forEach(wrap => {
            const theme = wrap.dataset.category;
            const anyVisible = Array.from(items).some(
                item => item.dataset.theme === theme && !item.classList.contains('hidden')
            );
            // masque tout le bloc (pas seulement le titre) pour ne pas laisser de gap-10 vide quand aucune question du thème n'est visible
            wrap.classList.toggle('hidden', !anyVisible);

            const heading = wrap.querySelector('[data-category-heading]');
            if (heading) {
                heading.classList.toggle('hidden', activeTheme === 'frequentes' || !anyVisible);
            }
        });

        if (frequentesHeading) {
            frequentesHeading.classList.toggle('hidden', activeTheme !== 'frequentes' || visibleCount === 0);
        }

        if (noResults) {
            noResults.classList.toggle('hidden', visibleCount > 0);
        }
    }

    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            chips.forEach(c => {
                c.classList.remove('is-active');
                c.setAttribute('aria-selected', 'false');
            });
            chip.classList.add('is-active');
            chip.setAttribute('aria-selected', 'true');
            activeTheme = chip.dataset.themeFilter;
            applyFilters();
        });
    });

    searchInput.addEventListener('input', applyFilters);
});
