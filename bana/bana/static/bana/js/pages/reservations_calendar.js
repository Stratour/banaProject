/**
 * Vue calendrier unifiée pour "Mes réservations" : les réservations effectuées
 * (role "made", la personne affichée est le conducteur) et les demandes reçues
 * (role "received", c'est le parent demandeur) y cohabitent.
 *
 * Le panneau du jour est ACTIONNABLE : une date ne porte qu'une réservation par
 * personne, les réponses y sont donc unitaires (pas de sélection multiple comme
 * dans la vue liste). Un yaya confirme ou refuse, un parent annule sa demande.
 * Les URLs et l'état à reposter viennent du serveur (entrées JSON + data-* du
 * conteneur) : ce fichier ne connaît ni le routage ni le contexte de gabarit.
 *
 * Toute la couleur/mise en forme dynamique est appliquée en inline style
 * (voir la note dans trajects_wizard.js — ce fichier n'est pas scanné par
 * le JIT Tailwind, donc les classes assemblées ici seraient purgées).
 *
 * Contrat HTML (voir reservation/partials/reservations_content.html) :
 *  - [data-tj-view-btn="list|calendar"] : boutons de bascule
 *  - [data-tj-view="list|calendar"]      : panneaux à afficher/masquer
 *  - [data-tj-resa-calendar]             : conteneur où le calendrier est injecté,
 *    porteur de data-tj-csrf / -tab / -made-page / -received-page / -next / -child-icon
 *  - #resa-calendar-data                 : json_script contenant la liste des entrées
 *    (cf. _calendar_entries dans trajects/views.py pour les clés)
 */
(function () {
  "use strict";

  const DAYS_FR = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];
  const MONTHS_FULL_FR = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"];
  const MONTHS_FR = ["jan", "fév", "mar", "avr", "mai", "jun", "jul", "aoû", "sep", "oct", "nov", "déc"];

  // `color` sert aux pastilles du calendrier, qui ne résument qu'un statut.
  // Le badge d'une carte, lui, vient du serveur (entry.status_label/bg/fg) :
  // ces valeurs ne sont plus qu'un repli si la clé manque.
  const STATUS_CFG = {
    confirmed: { label: "Confirmée", color: "#007F73", bg: "#D1FAE5", fg: "#065F46" },
    pending: { label: "En attente", color: "#F59E0B", bg: "#FEF3C7", fg: "#92400E" },
    canceled: { label: "Annulée", color: "#EF4444", bg: "#F3F4F6", fg: "#6B7280" },
  };

  // Qui est la personne affichée. Une ligne de texte discrète plutôt qu'une
  // pastille colorée : le calendrier mélange les deux flux, il faut le dire,
  // mais ce n'est pas une information de statut.
  const ROLE_LABEL = { made: "Votre demande", received: "Demande reçue" };

  const ICON_PIN =
    `<svg width='15' height='15' viewBox='0 0 24 24' fill='none' stroke='#007F73' stroke-width='2' style='flex-shrink:0;margin-top:1px;'>` +
    `<path stroke-linecap='round' stroke-linejoin='round' d='M12 11c1.657 0 3-1.343 3-3S13.657 5 12 5 9 6.343 9 8s1.343 3 3 3z'/>` +
    `<path stroke-linecap='round' stroke-linejoin='round' d='M12 22s8-4.5 8-12a8 8 0 10-16 0c0 7.5 8 12 8 12z'/></svg>`;

  const ICON_FLAG =
    `<svg width='15' height='15' viewBox='0 0 24 24' fill='none' stroke='#007F73' stroke-width='2' style='flex-shrink:0;margin-top:1px;'>` +
    `<path stroke-linecap='round' stroke-linejoin='round' d='M5 5v14M5 5h10l-2 4 2 4H5'/></svg>`;

  const ICON_RADIUS =
    `<svg width='15' height='15' viewBox='0 0 24 24' fill='none' stroke='#007F73' style='flex-shrink:0;margin-top:1px;'>` +
    `<circle cx='12' cy='12' r='8' stroke-width='2'/><circle cx='12' cy='12' r='2.5' fill='#007F73' stroke='none'/></svg>`;

  const ICON_CHECK =
    `<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'>` +
    `<path d='M5 13l4 4L19 7'/></svg>`;

  const ICON_CROSS =
    `<svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='3' stroke-linecap='round'>` +
    `<path d='M6 6l12 12M18 6L6 18'/></svg>`;

  // Vue courante et jour ouvert, conservés hors du DOM : après une action, HTMX
  // remplace tout le bloc et on doit revenir exactement où l'utilisateur était.
  const uiState = { view: "list", iso: null };

  function pad2(n) {
    return String(n).padStart(2, "0");
  }

  function claim(el, key) {
    if (el.dataset[key]) return false;
    el.dataset[key] = "1";
    return true;
  }

  // Le panneau est assemblé en innerHTML : adresses, noms de trajet et noms de
  // personnes viennent de la base et doivent être échappés.
  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[c]);
  }

  function applyView(root, view) {
    root.querySelectorAll("[data-tj-view]").forEach((v) => {
      v.classList.toggle("hidden", v.getAttribute("data-tj-view") !== view);
    });
    root.querySelectorAll("[data-tj-view-btn]").forEach((b) => {
      const active = b.getAttribute("data-tj-view-btn") === view;
      b.style.background = active ? "#007F73" : "transparent";
      b.style.color = active ? "#fff" : "#A0A09A";
    });
  }

  function initToggle(root) {
    if (!claim(root, "tjViewBound")) return;
    root.querySelectorAll("[data-tj-view-btn]").forEach((btn) => {
      btn.addEventListener("click", () => {
        uiState.view = btn.getAttribute("data-tj-view-btn");
        applyView(root, uiState.view);
      });
    });
    applyView(root, uiState.view);
  }

  function initCalendar(root) {
    const container = root.querySelector("[data-tj-resa-calendar]");
    const dataEl = root.querySelector("#resa-calendar-data");
    if (!container || !dataEl || !claim(container, "tjCalBound")) return;

    let entries = [];
    try {
      entries = JSON.parse(dataEl.textContent);
    } catch (e) {
      entries = [];
    }

    const byIso = {};
    entries.forEach((e) => {
      if (!byIso[e.iso]) byIso[e.iso] = [];
      byIso[e.iso].push(e);
    });

    const ds = container.dataset;
    // Mêmes champs que action_state_fields.html : sans eux, la vue reconstruit
    // le contexte sur l'onglet "active", page 1, et l'écran saute.
    const stateFields =
      `<input type="hidden" name="csrfmiddlewaretoken" value="${esc(ds.tjCsrf)}">` +
      `<input type="hidden" name="open_key" value="">` +
      `<input type="hidden" name="tab" value="${esc(ds.tjTab)}">` +
      `<input type="hidden" name="made_page" value="${esc(ds.tjMadePage)}">` +
      `<input type="hidden" name="received_page" value="${esc(ds.tjReceivedPage)}">` +
      `<input type="hidden" name="next" value="${esc(ds.tjNext)}">`;

    const today = new Date();
    const todayIso = `${today.getFullYear()}-${pad2(today.getMonth() + 1)}-${pad2(today.getDate())}`;

    // Le jour retenu d'avant l'action peut avoir disparu de l'onglet courant.
    let selectedIso = uiState.iso && byIso[uiState.iso] ? uiState.iso : null;
    uiState.iso = selectedIso;

    let year = today.getFullYear();
    let month = today.getMonth();
    const isoList = Object.keys(byIso).sort();
    if (selectedIso) {
      const [y, m] = selectedIso.split("-").map(Number);
      year = y; month = m - 1;
    } else if (isoList.length) {
      // Sinon on démarre sur le mois de la plus proche à venir (ou la plus récente).
      const pick = isoList.find((iso) => iso >= todayIso) || isoList[isoList.length - 1];
      const [y, m] = pick.split("-").map(Number);
      year = y; month = m - 1;
    }

    /** Un bouton d'action, dans son propre formulaire (l'action est dans l'URL).
     *  `confirmMsg` déclenche la confirmation native d'HTMX avant l'envoi. */
    function actionForm(url, label, inner, confirmMsg) {
      const confirmAttr = confirmMsg ? ` hx-confirm="${esc(confirmMsg)}"` : "";
      return `<form method="post" action="${esc(url)}" hx-post="${esc(url)}"` +
        ` hx-target="#reservations-content" hx-swap="outerHTML"${confirmAttr}` +
        ` style="display:inline-flex;margin:0;">${stateFields}` +
        `<button type="submit" title="${esc(label)}" aria-label="${esc(label)}">${inner}</button></form>`;
    }

    const BTN_BASE = "width:40px;height:40px;border-radius:11px;display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;";

    function entryActions(entry, dateLabel) {
      if (!entry.can_act) {
        // Libellé et couleurs calculés côté serveur (_status_badge) : « Annulée
        // par vous » et « Refusée » ne se déduisent pas du seul statut. Le
        // libellé peut faire deux lignes, d'où l'absence de nowrap.
        const cfg = STATUS_CFG[entry.status] || STATUS_CFG.pending;
        return `<span style="padding:5px 12px;border-radius:24px;font-size:11px;font-weight:700;` +
          `background:${esc(entry.status_bg || cfg.bg)};color:${esc(entry.status_fg || cfg.fg)};` +
          `text-align:right;max-width:150px;flex-shrink:0;">${esc(entry.status_label || cfg.label)}</span>`;
      }
      const reject = `<span style="${BTN_BASE}border:1.5px solid #FCA5A5;background:#fff;color:#DC2626;">${ICON_CROSS}</span>`;
      if (entry.role === "received") {
        const accept = `<span style="${BTN_BASE}border:none;background:#007F73;color:#fff;">${ICON_CHECK}</span>`;
        return `<div style="display:flex;gap:8px;flex-shrink:0;">` +
          actionForm(entry.reject_url, "Refuser cette demande", reject) +
          actionForm(entry.accept_url, "Confirmer cette demande", accept) +
          `</div>`;
      }
      // Côté parent, la seule réponse possible est de retirer sa demande.
      // Confirmation obligatoire : le bouton est une icône de 40px sur mobile,
      // l'action est irréversible et il faudrait tout redemander.
      const ask = `Annuler votre demande du ${dateLabel} auprès de ${entry.person} ?`
        + ` Cette action est définitive : il faudra envoyer une nouvelle demande.`;
      return `<div style="display:flex;flex-shrink:0;">` +
        actionForm(entry.cancel_url, "Annuler ma demande", reject, ask) +
        `</div>`;
    }

    function routeLine(icon, text, time) {
      if (!text) return "";
      const hour = time
        ? ` <span style="color:#6B7280;font-size:11.5px;white-space:nowrap;">( ${esc(time)} )</span>`
        : "";
      return `<span style="display:flex;align-items:flex-start;gap:6px;min-width:0;">${icon}` +
        `<span style="min-width:0;">${esc(text)}${hour}</span></span>`;
    }

    function entryCard(entry, dateLabel) {
      let html = `<div style="background:#fff;border-radius:12px;border:1px solid #EDEDEA;padding:12px 14px;display:flex;flex-direction:column;gap:10px;">`;

      // Identité + actions, toujours sur une seule ligne, y compris en 360px :
      // l'avatar et les boutons ont une largeur fixe, seul le nom se tronque.
      html += `<div style="display:flex;align-items:center;gap:10px;">`;
      html += `<span style="position:relative;width:38px;height:38px;flex-shrink:0;display:block;">`;
      html += `<img src="${esc(entry.avatar)}" alt="" style="width:38px;height:38px;border-radius:50%;object-fit:cover;background:#E9F5F1;">`;
      if (entry.verified) {
        html += `<span style="position:absolute;top:-3px;left:-3px;width:15px;height:15px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 3px rgba(0,0,0,0.2);">` +
          `<svg width='13' height='13' viewBox='0 0 24 24' fill='none'><circle cx='12' cy='12' r='10' fill='#007F73'/>` +
          `<path d='M7 12l3 3 7-7' stroke='#fff' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'/></svg></span>`;
      }
      html += `</span>`;
      html += `<span style="flex:1;min-width:0;display:block;">` +
        `<span style="display:block;font-size:13.5px;font-weight:800;color:#0F0F0F;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${esc(entry.person || "—")}</span>` +
        `<span style="display:block;font-size:11px;color:#9CA3AF;font-weight:500;">${ROLE_LABEL[entry.role] || ""}</span>` +
        `</span>`;
      html += entryActions(entry, dateLabel);
      html += `</div>`;

      // Itinéraire, même grammaire que la vue liste : une ligne par point.
      html += `<div style="border-top:1px solid #F3F4F6;padding-top:9px;display:flex;flex-direction:column;gap:6px;font-size:12.5px;color:#374151;line-height:1.35;">`;
      html += routeLine(ICON_PIN, entry.depart, entry.depart_time);
      if (entry.is_simple) {
        html += `<span style="display:flex;align-items:flex-start;gap:6px;color:#007F73;font-weight:600;">${ICON_RADIUS}` +
          `<span>Dans un rayon de ${esc(entry.radius_km || 5)} km</span></span>`;
      } else {
        html += routeLine(ICON_FLAG, entry.arrivee, entry.arrivee_time);
      }
      html += `</div>`;

      if (entry.children && entry.children.length) {
        html += `<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">`;
        html += `<img src="${esc(ds.tjChildIcon)}" alt="Enfants" style="width:20px;height:16px;flex-shrink:0;">`;
        entry.children.forEach((child) => {
          const age = child.age ? ` <span style="color:#6B7280;font-weight:400;">— ${esc(child.age)} ans</span>` : "";
          html += `<span style="display:inline-flex;align-items:center;border:1.5px solid #E5E7EB;border-radius:999px;padding:3px 10px;font-size:11.5px;font-weight:600;color:#374151;">${esc(child.label)}${age}</span>`;
        });
        html += `</div>`;
      }

      html += `</div>`;
      return html;
    }

    function render() {
      const firstDow = new Date(year, month, 1).getDay();
      const offset = firstDow === 0 ? 6 : firstDow - 1;
      const daysInMonth = new Date(year, month + 1, 0).getDate();
      const cells = [];
      for (let i = 0; i < offset; i++) cells.push(null);
      for (let d = 1; d <= daysInMonth; d++) cells.push(d);
      while (cells.length % 7 !== 0) cells.push(null);

      const isToday = (d) => d === today.getDate() && month === today.getMonth() && year === today.getFullYear();

      let html = "";
      html += `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">`;
      html += `<button type="button" data-tj-rc-prev aria-label="Mois précédent" style="width:34px;height:34px;border-radius:9px;border:1.5px solid #E5E7EB;background:#fff;color:#6B7280;cursor:pointer;">←</button>`;
      html += `<span style="font-weight:800;font-size:16px;color:#0F0F0F;">${MONTHS_FULL_FR[month]} ${year}</span>`;
      html += `<button type="button" data-tj-rc-next aria-label="Mois suivant" style="width:34px;height:34px;border-radius:9px;border:1.5px solid #E5E7EB;background:#fff;color:#6B7280;cursor:pointer;">→</button>`;
      html += `</div>`;

      html += `<div style="display:grid;grid-template-columns:repeat(7,1fr);margin-bottom:6px;">`;
      ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"].forEach((x) => {
        html += `<div style="text-align:center;font-size:10px;font-weight:700;color:#9CA3AF;letter-spacing:0.06em;padding-bottom:8px;">${x}</div>`;
      });
      html += `</div>`;

      html += `<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:3px 2px;">`;
      cells.forEach((d) => {
        if (!d) { html += `<div></div>`; return; }
        const iso = `${year}-${pad2(month + 1)}-${pad2(d)}`;
        const dayEntries = byIso[iso] || [];
        const hasEntries = dayEntries.length > 0;
        const isSelected = iso === selectedIso;
        const td = isToday(d) && !isSelected;

        let cellStyle = "display:flex;flex-direction:column;align-items:center;gap:4px;padding:9px 4px 8px;border-radius:10px;min-height:54px;";
        cellStyle += hasEntries ? "cursor:pointer;" : "cursor:default;";
        cellStyle += `background:${isSelected ? "#007F73" : (td ? "#E6F5F3" : "transparent")};`;
        cellStyle += `border:1.5px solid ${td ? "#007F73" : "transparent"};`;

        const numColor = isSelected ? "#fff" : (td ? "#007F73" : (hasEntries ? "#1C1C1C" : "#BABAB5"));
        const numWeight = hasEntries || td || isSelected ? "700" : "400";

        let dots = "";
        if (hasEntries) {
          const statuses = [...new Set(dayEntries.map((e) => e.status))];
          dots = `<div style="display:flex;gap:4px;justify-content:center;flex-wrap:wrap;">` +
            statuses.map((st) => {
              const cfg = STATUS_CFG[st] || STATUS_CFG.pending;
              const dotColor = isSelected ? "rgba(255,255,255,0.85)" : cfg.color;
              return `<div style="width:10px;height:10px;border-radius:50%;background:${dotColor};box-shadow:${isSelected ? "none" : "0 1px 3px rgba(0,0,0,0.18)"};"></div>`;
            }).join("") + `</div>`;
        }

        html += `<div class="tj-cal-cell" data-tj-rc-day="${hasEntries ? iso : ""}" style="${cellStyle}">` +
          `<span style="font-size:14px;line-height:1;color:${numColor};font-weight:${numWeight};">${d}</span>` +
          dots +
          `</div>`;
      });
      html += `</div>`;

      html += `<div style="display:flex;gap:16px;margin-top:20px;padding-top:16px;border-top:1px solid #F3F4F6;flex-wrap:wrap;">`;
      [["#007F73", "Confirmée"], ["#F59E0B", "En attente"], ["#EF4444", "Annulée"]].forEach(([col, lbl]) => {
        html += `<div style="display:flex;align-items:center;gap:6px;">` +
          `<div style="width:8px;height:8px;border-radius:50%;background:${col};"></div>` +
          `<span style="font-size:11px;color:#9CA3AF;font-weight:500;">${lbl}</span></div>`;
      });
      html += `</div>`;

      if (selectedIso && byIso[selectedIso]) {
        const [sy, sm, sd] = selectedIso.split("-").map(Number);
        const dateObj = new Date(sy, sm - 1, sd);
        const dateLabel = `${DAYS_FR[dateObj.getDay()]} ${sd} ${MONTHS_FR[sm - 1]} ${sy}`;

        html += `<div style="margin-top:18px;background:#F8FAF9;border-radius:14px;border:1px solid #E5E4DF;padding:14px;">` +
          `<p style="font-size:13px;font-weight:800;color:#007F73;margin:0 0 12px;">${dateLabel}</p>` +
          `<div style="display:flex;flex-direction:column;gap:10px;">` +
          byIso[selectedIso].map((entry) => entryCard(entry, dateLabel)).join("") +
          `</div></div>`;
      }

      container.innerHTML = html;
      // Les formulaires viennent d'être créés : HTMX ne les connaît pas encore.
      if (window.htmx) window.htmx.process(container);

      const prevBtn = container.querySelector("[data-tj-rc-prev]");
      const nextBtn = container.querySelector("[data-tj-rc-next]");
      if (prevBtn) prevBtn.addEventListener("click", () => { month--; if (month < 0) { month = 11; year--; } render(); });
      if (nextBtn) nextBtn.addEventListener("click", () => { month++; if (month > 11) { month = 0; year++; } render(); });

      container.querySelectorAll("[data-tj-rc-day]").forEach((cell) => {
        const iso = cell.getAttribute("data-tj-rc-day");
        if (!iso) return;
        cell.addEventListener("click", () => {
          selectedIso = selectedIso === iso ? null : iso;
          uiState.iso = selectedIso;
          render();
        });
      });
    }

    render();
  }

  function initAll() {
    document.querySelectorAll("[data-tj-resa-app]").forEach((root) => {
      initToggle(root);
      initCalendar(root);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }

  // Le bloc [data-tj-resa-app] est remplacé en entier par HTMX (hx-swap="outerHTML")
  // à chaque changement d'onglet / page / action — on ré-attache les écouteurs sur
  // le nouveau nœud, et uiState ramène l'utilisateur sur sa vue et son jour.
  document.body.addEventListener("htmx:afterSwap", initAll);
})();
