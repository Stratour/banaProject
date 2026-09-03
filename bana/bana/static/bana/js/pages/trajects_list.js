/**
 * Accordéon "Voir les dates" sur les pages "Mes trajets" (liste des groupes).
 * Toutes les dates sont déjà rendues côté serveur (au-delà de 7, elles portent
 * juste la classe "hidden") — ce script ne fait que basculer leur visibilité,
 * sans requête réseau ni changement d'URL.
 *
 * NOTE : on bascule la classe Tailwind "hidden", jamais l'attribut HTML natif
 * [hidden] — ces lignes portent aussi "flex" (même spécificité CSS), et le
 * navigateur donne la priorité à la feuille de style auteur (Tailwind) sur sa
 * propre feuille par défaut : l'attribut natif serait silencieusement ignoré
 * et la ligne resterait visible.
 *
 * Contrat HTML :
 *  - bouton toggle   : [data-tj-toggle-dates] avec un enfant [data-tj-toggle-label]
 *  - panneau associé : [data-tj-dates-panel], plus proche ancêtre commun avec le bouton
 *  - lignes cachées  : [data-tj-date-extra] à l'intérieur du panneau
 *  - bouton "voir plus" : [data-tj-show-more], à l'intérieur du panneau
 */
(function () {
  "use strict";

  document.querySelectorAll("[data-tj-toggle-dates]").forEach((btn) => {
    const card = btn.closest("article") || btn.parentElement;
    const panel = card ? card.querySelector("[data-tj-dates-panel]") : null;
    if (!panel) return;
    const label = btn.querySelector("[data-tj-toggle-label]");

    btn.addEventListener("click", () => {
      const willShow = panel.classList.contains("hidden");
      panel.classList.toggle("hidden", !willShow);
      if (label) label.textContent = willShow ? "Masquer les dates ↑" : "Voir les dates ↓";
    });
  });

  document.querySelectorAll("[data-tj-show-more]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const panel = btn.closest("[data-tj-dates-panel]");
      if (!panel) return;
      panel.querySelectorAll("[data-tj-date-extra]").forEach((row) => row.classList.remove("hidden"));
      btn.classList.add("hidden");
    });
  });

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
  document.querySelectorAll("[data-tj-bulk-form]").forEach((form) => {
    const checkboxes = Array.from(form.querySelectorAll("[data-tj-bulk-checkbox]"));
    const selectAllBtn = form.querySelector("[data-tj-select-all]");
    const submitBtn = form.querySelector("[data-tj-bulk-submit]");
    const countEl = form.querySelector("[data-tj-bulk-count]");
    if (!checkboxes.length || !submitBtn) return;

    const updateState = () => {
      const checkedCount = checkboxes.filter((cb) => cb.checked).length;
      if (countEl) countEl.textContent = String(checkedCount);
      submitBtn.disabled = checkedCount === 0;
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
})();
