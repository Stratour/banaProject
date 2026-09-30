/**
 * Accordéon "Voir les dates" sur les pages "Mes trajets", "Mes matchings" et
 * "Mes réservations". Toutes les dates sont déjà rendues côté serveur — ce
 * script ne fait que basculer leur visibilité, sans requête réseau ni
 * changement d'URL.
 *
 * NOTE : on bascule la classe Tailwind "hidden", jamais l'attribut HTML natif
 * [hidden] — ces lignes portent aussi "flex" (même spécificité CSS), et le
 * navigateur donne la priorité à la feuille de style auteur (Tailwind) sur sa
 * propre feuille par défaut : l'attribut natif serait silencieusement ignoré
 * et la ligne resterait visible.
 *
 * Contrat HTML :
 *  - bouton toggle   : [data-tj-toggle-dates] avec un enfant [data-tj-toggle-label],
 *                      et les libellés dans data-tj-label-show / data-tj-label-hide
 *  - panneau associé : [data-tj-dates-panel], dans le même <article> que le bouton
 */
(function () {
  "use strict";

  // Sur la page réservations, le bloc entier est remplacé par HTMX à chaque
  // onglet / page / action : initAll() est rejoué sur le nouveau DOM. Le drapeau
  // évite de ré-attacher deux fois les écouteurs sur les nœuds déjà vus.
  function claim(el) {
    if (el.dataset.tjBound) return false;
    el.dataset.tjBound = "1";
    return true;
  }

  function initToggles() {
    document.querySelectorAll("[data-tj-toggle-dates]").forEach((btn) => {
      const card = btn.closest("article") || btn.parentElement;
      const panel = card ? card.querySelector("[data-tj-dates-panel]") : null;
      if (!panel || !claim(btn)) return;

      const label = btn.querySelector("[data-tj-toggle-label]");
      const showText = btn.dataset.tjLabelShow || "Voir les dates ↓";
      const hideText = btn.dataset.tjLabelHide || "Masquer les dates ↑";

      btn.addEventListener("click", () => {
        const willShow = panel.classList.contains("hidden");
        panel.classList.toggle("hidden", !willShow);
        if (label) label.textContent = willShow ? hideText : showText;
      });
    });
  }

  /**
   * Sélection multiple des dates réservables dans un panneau de matching
   * (page "Mes matchings" côté parent) : coche plusieurs dates puis envoie
   * une seule réservation groupée au lieu de cliquer "Réserver" par date.
   *
   * Contrat HTML (par formulaire [data-tj-bulk-form]) :
   *  - cases à cocher              : [data-tj-bulk-checkbox]
   *  - bouton "tout sélectionner"  : [data-tj-select-all]
   *  - bouton "Réserver"           : [data-tj-bulk-submit]
   *  - compteur dans le bouton     : [data-tj-bulk-count]
   */
  function initBulkForms() {
    document.querySelectorAll("[data-tj-bulk-form]").forEach((form) => {
      const checkboxes = Array.from(form.querySelectorAll("[data-tj-bulk-checkbox]"));
      const selectAllBtn = form.querySelector("[data-tj-select-all]");
      // Plusieurs boutons possibles dans un même formulaire : côté yaya on
      // répond « Confirmer » ou « Refuser » sur la même sélection de dates.
      const submitBtns = Array.from(form.querySelectorAll("[data-tj-bulk-submit]"));
      const countEls = Array.from(form.querySelectorAll("[data-tj-bulk-count]"));
      if (!checkboxes.length || !submitBtns.length || !claim(form)) return;

      const updateState = () => {
        const checkedCount = checkboxes.filter((cb) => cb.checked).length;
        countEls.forEach((el) => { el.textContent = String(checkedCount); });
        submitBtns.forEach((btn) => { btn.disabled = checkedCount === 0; });
        if (selectAllBtn) {
          selectAllBtn.textContent = checkedCount === checkboxes.length ? "Tout désélectionner" : "Tout sélectionner";
        }
      };

      checkboxes.forEach((cb) => cb.addEventListener("change", updateState));

      if (selectAllBtn) {
        selectAllBtn.addEventListener("click", () => {
          const allChecked = checkboxes.every((cb) => cb.checked);
          checkboxes.forEach((cb) => { cb.checked = !allChecked; });
          updateState();
        });
      }

      updateState();
    });
  }

  function initAll() {
    initToggles();
    initBulkForms();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }

  document.body.addEventListener("htmx:afterSwap", initAll);
})();
