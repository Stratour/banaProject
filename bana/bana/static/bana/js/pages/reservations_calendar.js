/**
 * Vue calendrier pour "Mes réservations" (côté Parent).
 * Toute la couleur/mise en forme dynamique est appliquée en inline style
 * (voir la note dans trajects_wizard.js — ce fichier n'est pas scanné par
 * le JIT Tailwind, donc les classes assemblées ici seraient purgées).
 *
 * Contrat HTML (voir reservation/partials/reservations_content.html) :
 *  - [data-tj-view-btn="list|calendar"] : boutons de bascule
 *  - [data-tj-view="list|calendar"]      : panneaux à afficher/masquer
 *  - [data-tj-resa-calendar]             : conteneur où le calendrier est injecté
 *  - #resa-calendar-data                 : json_script contenant la liste des entrées
 *    [{ iso, status, trip, depart, arrivee, heure, yaya, initials }, ...]
 */
(function () {
  "use strict";

  const DAYS_FR = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];
  const MONTHS_FULL_FR = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"];
  const MONTHS_FR = ["jan", "fév", "mar", "avr", "mai", "jun", "jul", "aoû", "sep", "oct", "nov", "déc"];

  const STATUS_CFG = {
    confirmed: { label: "Confirmé", color: "#007F73", bg: "#D1FAE5", fg: "#065F46" },
    pending: { label: "En attente", color: "#F59E0B", bg: "#FEF3C7", fg: "#92400E" },
    canceled: { label: "Annulée", color: "#EF4444", bg: "#FEE2E2", fg: "#991B1B" },
  };

  function pad2(n) {
    return String(n).padStart(2, "0");
  }

  // Couleur déterministe par nom (pas de champ couleur en base).
  function colorFor(seed) {
    const palette = ["#007F73", "#5B4E8C", "#B55A20", "#1E6B8C", "#8C5B4E", "#2E7D5B"];
    let hash = 0;
    for (let i = 0; i < seed.length; i++) hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
    return palette[hash % palette.length];
  }

  function initToggle(root) {
    const buttons = root.querySelectorAll("[data-tj-view-btn]");
    const views = root.querySelectorAll("[data-tj-view]");
    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.getAttribute("data-tj-view-btn");
        views.forEach((v) => v.classList.toggle("hidden", v.getAttribute("data-tj-view") !== target));
        buttons.forEach((b) => {
          const active = b === btn;
          b.style.background = active ? "#007F73" : "transparent";
          b.style.color = active ? "#fff" : "#A0A09A";
        });
      });
    });
  }

  function initCalendar(root) {
    const container = root.querySelector("[data-tj-resa-calendar]");
    const dataEl = root.querySelector("#resa-calendar-data");
    if (!container || !dataEl) return;

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

    const today = new Date();
    let year = today.getFullYear();
    let month = today.getMonth();
    // Si des réservations existent, on démarre sur le mois de la plus proche à venir (ou la plus récente).
    const isoList = Object.keys(byIso).sort();
    if (isoList.length) {
      const upcoming = isoList.find((iso) => iso >= `${today.getFullYear()}-${pad2(today.getMonth() + 1)}-${pad2(today.getDate())}`);
      const pick = upcoming || isoList[isoList.length - 1];
      const [y, m] = pick.split("-").map(Number);
      year = y; month = m - 1;
    }
    let selectedIso = null;

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
      html += `<button type="button" data-tj-rc-prev style="width:32px;height:32px;border-radius:8px;border:1.5px solid #E5E7EB;background:#fff;color:#6B7280;cursor:pointer;">←</button>`;
      html += `<span style="font-weight:800;font-size:16px;color:#0F0F0F;">${MONTHS_FULL_FR[month]} ${year}</span>`;
      html += `<button type="button" data-tj-rc-next style="width:32px;height:32px;border-radius:8px;border:1.5px solid #E5E7EB;background:#fff;color:#6B7280;cursor:pointer;">→</button>`;
      html += `</div>`;

      html += `<div style="display:grid;grid-template-columns:repeat(7,1fr);margin-bottom:6px;">`;
      ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"].forEach((x) => {
        html += `<div style="text-align:center;font-size:10px;font-weight:700;color:#C0BFBA;letter-spacing:0.06em;padding-bottom:8px;">${x}</div>`;
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

        let panel = `<div style="margin-top:20px;background:#F8FAF9;border-radius:14px;border:1px solid #E5E4DF;padding:18px 20px;">`;
        panel += `<p style="font-size:13px;font-weight:700;color:#007F73;margin-bottom:14px;">${dateLabel}</p>`;
        panel += `<div style="display:flex;flex-direction:column;gap:8px;">`;
        byIso[selectedIso].forEach((entry) => {
          const cfg = STATUS_CFG[entry.status] || STATUS_CFG.pending;
          const col = colorFor(entry.yaya || entry.trip || "?");
          panel += `<div style="background:#fff;border-radius:12px;border:1px solid #EDEDEA;overflow:hidden;">`;
          panel += `<div style="display:flex;align-items:center;gap:12px;padding:14px 16px;border-bottom:1px solid #F3F4F6;">`;
          panel += `<div style="width:38px;height:38px;border-radius:50%;background:${col};color:#fff;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;flex-shrink:0;">${entry.initials || "?"}</div>`;
          panel += `<div style="flex:1;min-width:0;">`;
          panel += `<span style="font-size:13px;font-weight:700;color:#0F0F0F;">${entry.yaya || "—"}</span>`;
          panel += `</div>`;
          panel += `<span style="padding:4px 12px;border-radius:24px;font-size:11px;font-weight:700;background:${cfg.bg};color:${cfg.fg};white-space:nowrap;">${cfg.label}</span>`;
          panel += `</div>`;
          panel += `<div style="padding:12px 16px;display:flex;flex-direction:column;gap:6px;">`;
          panel += `<p style="font-size:12px;color:#6B7280;">${entry.depart || ""} <span style="color:#007F73;font-weight:700;">→</span> ${entry.arrivee || ""}</p>`;
          panel += `<p style="font-size:12px;color:#9CA3AF;">${entry.trip || ""} · ${entry.heure || ""}</p>`;
          panel += `</div></div>`;
        });
        panel += `</div></div>`;
        html += panel;
      }

      container.innerHTML = html;

      const prevBtn = container.querySelector("[data-tj-rc-prev]");
      const nextBtn = container.querySelector("[data-tj-rc-next]");
      if (prevBtn) prevBtn.addEventListener("click", () => { month--; if (month < 0) { month = 11; year--; } render(); });
      if (nextBtn) nextBtn.addEventListener("click", () => { month++; if (month > 11) { month = 0; year++; } render(); });

      container.querySelectorAll("[data-tj-rc-day]").forEach((cell) => {
        const iso = cell.getAttribute("data-tj-rc-day");
        if (!iso) return;
        cell.addEventListener("click", () => {
          selectedIso = selectedIso === iso ? null : iso;
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
  // à chaque changement d'onglet / page — on ré-attache les écouteurs sur le nouveau nœud.
  document.body.addEventListener("htmx:afterSwap", initAll);
})();
