/**
 * Wizard 3 étapes + calendrier interactif, partagé par les pages
 * "Nouveau trajet" de proposition/, proposition_rayon/ et recherche/.
 *
 * NOTE : tout le style visuel dynamique ici est appliqué via `element.style.*`
 * (jamais via classList.add d'une classe Tailwind arbitraire) car ce fichier
 * n'est pas scanné par le JIT Tailwind (seuls les *.html et *.py le sont) —
 * une classe assemblée uniquement ici serait purgée du CSS compilé.
 *
 * Contrat HTML attendu (voir les templates creer.html) :
 *  - conteneur racine  : [data-tj-wizard]
 *  - étapes            : [data-tj-step="1|2|3"]
 *  - libellés étapes   : [data-tj-step-label="1|2|3"]
 *  - cercles étapes    : [data-tj-step-circle="1|2|3"]
 *  - ligne de progrès  : [data-tj-step-line-fill]
 *  - boutons           : [data-tj-next] [data-tj-prev]
 *  - groupe requis     : [data-tj-pill-group][data-tj-require-checked] + un
 *                        <p data-tj-pill-error> frère, affiché si rien n'est coché
 *  - pills jour        : #weekday-selector label[data-tj-pill] > input[name="tr_weekdays"]
 *  - pills génériques  : [data-tj-pill-group] label[data-tj-pill] > input
 *  - radios récurrence : input[name="recurrence_type"] (one_week | weekly | biweekly)
 *  - jours wrapper     : #weekdays_container (visible seulement weekly/biweekly)
 *  - calendrier        : [data-tj-calendar]
 *  - récap (mode libre): [data-tj-recap]
 *
 *  Calendrier avancé (optionnel — activé si les éléments suivants sont présents,
 *  sinon on retombe sur l'ancien comportement en lecture seule pour les pages
 *  qui n'ont pas encore ce balisage) :
 *  - plage de dates    : #daterange_container (contient date_debut ET date_fin,
 *                        masqué entièrement en mode "one_week")
 *  - dates sélectionnées (mode one_week, sélection libre) :
 *                        [data-tj-selected-input] (input hidden, CSV de dates ISO)
 *  - dates exclues (mode weekly/biweekly) :
 *                        [data-tj-excluded-input] (input hidden, CSV de dates ISO)
 *  - panneau d'exclusion : [data-tj-excluded-panel] / [data-tj-excluded-summary] /
 *                        [data-tj-excluded-counter] / [data-tj-excluded-list]
 */
(function () {
  "use strict";

  const BRAND = "#007F73";
  const BRAND_LIGHT = "#E6F5F3";
  const BRAND_MID = "#4DA89E";
  const BORDER = "#E5E7EB";
  const TEXT_MUTED = "#6B7280";
  const TEXT_DIM = "#B5B4AE";

  const DAYS_FR = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];
  const MONTHS_FR = ["jan", "fév", "mar", "avr", "mai", "jun", "jul", "aoû", "sep", "oct", "nov", "déc"];
  const MONTHS_FULL_FR = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"];

  function pad2(n) {
    return String(n).padStart(2, "0");
  }

  function isoOf(d) {
    return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
  }

  function parseIso(s) {
    if (!s) return null;
    const [y, m, d] = s.split("-").map(Number);
    if (!y || !m || !d) return null;
    return new Date(y, m - 1, d);
  }

  // Reproduit fidèlement trajects.views.generate_recurrent_dates côté client,
  // uniquement pour la prévisualisation (le serveur reste la source de vérité).
  function computeDates(recurrence, selectedDays, dateDebut, dateFin) {
    if (!dateDebut) return [];
    if (!dateFin) dateFin = dateDebut;
    if (dateDebut > dateFin) return [];

    const days = selectedDays.length
      ? selectedDays.slice().sort((a, b) => a - b)
      : [dateDebut.getDay() === 0 ? 7 : dateDebut.getDay()];

    const oneDay = 86400000;
    const dates = [];

    if (recurrence === "one_week" || !recurrence) {
      let cur = new Date(dateDebut);
      while (cur <= dateFin) {
        const dow = cur.getDay() === 0 ? 7 : cur.getDay();
        if (days.includes(dow)) dates.push(new Date(cur));
        cur = new Date(cur.getTime() + oneDay);
      }
      return dates;
    }

    const stepDays = recurrence === "weekly" ? 7 : recurrence === "biweekly" ? 14 : null;
    if (!stepDays) return [new Date(dateDebut)];

    days.forEach((targetDay) => {
      const targetWeekdayMon0 = targetDay - 1;
      const debutWeekdayMon0 = (dateDebut.getDay() + 6) % 7;
      const delta = ((targetWeekdayMon0 - debutWeekdayMon0) % 7 + 7) % 7;
      let cur = new Date(dateDebut.getTime() + delta * oneDay);
      while (cur <= dateFin) {
        dates.push(new Date(cur));
        cur = new Date(cur.getTime() + stepDays * oneDay);
      }
    });

    dates.sort((a, b) => a - b);
    return dates;
  }

  function fmtDate(d) {
    return `${DAYS_FR[d.getDay()]} ${d.getDate()} ${MONTHS_FR[d.getMonth()]}`;
  }

  const PILL_ACTIVE = { borderColor: BRAND, borderWidth: "2px", background: BRAND_LIGHT, color: BRAND, fontWeight: "700" };
  const PILL_INACTIVE = { borderColor: BORDER, borderWidth: "1.5px", background: "#fff", color: "#374151", fontWeight: "500" };
  const DAY_PILL_ACTIVE = { borderColor: BRAND, borderWidth: "1.5px", background: BRAND, color: "#fff", fontWeight: "700" };
  const DAY_PILL_INACTIVE = { borderColor: "#F3F4F6", borderWidth: "1.5px", background: "#F3F4F6", color: TEXT_MUTED, fontWeight: "500" };

  function initPillGroup(container, activeStyle, inactiveStyle) {
    if (!container) return;
    const labels = container.querySelectorAll("label[data-tj-pill]");
    function refresh() {
      labels.forEach((label) => {
        const input = label.querySelector("input");
        const isChecked = !!(input && input.checked);
        Object.assign(label.style, isChecked ? activeStyle : inactiveStyle);
      });
    }
    labels.forEach((label) => {
      const input = label.querySelector("input");
      if (input) input.addEventListener("change", refresh);
    });
    refresh();
    return refresh;
  }

  function initWizard(root) {
    const steps = Array.from(root.querySelectorAll("[data-tj-step]"));
    if (!steps.length) return;

    let current = 1;
    const total = steps.length;

    function circleFor(n) {
      return root.querySelector(`[data-tj-step-circle="${n}"]`);
    }
    function labelFor(n) {
      return root.querySelector(`[data-tj-step-label="${n}"]`);
    }

    function render() {
      steps.forEach((stepEl) => {
        const n = parseInt(stepEl.getAttribute("data-tj-step"), 10);
        stepEl.classList.toggle("hidden", n !== current);
      });

      for (let n = 1; n <= total; n++) {
        const circle = circleFor(n);
        const label = labelFor(n);
        if (circle) {
          if (n < current) {
            Object.assign(circle.style, { background: BRAND, color: "#fff", border: "none" });
            circle.textContent = "✓";
          } else if (n === current) {
            Object.assign(circle.style, { background: "#fff", color: BRAND, border: `2.5px solid ${BRAND}` });
            circle.textContent = String(n);
          } else {
            Object.assign(circle.style, { background: "#E5E4DF", color: "#A0A09A", border: "none" });
            circle.textContent = String(n);
          }
        }
        if (label) {
          label.style.color = n <= current ? BRAND : TEXT_DIM;
        }
      }

      const fill = root.querySelector("[data-tj-step-line-fill]");
      if (fill) {
        const progress = total > 1 ? (current - 1) / (total - 1) : 0;
        // 36px = diamètre des cercles d'étape (cf. data-tj-step-circle dans creer.html) :
        // la ligne de progrès doit s'arrêter au centre du cercle, pas déborder dessus.
        fill.style.width = `calc((100% - 36px) * ${progress})`;
      }
    }

    function showPillError(group, show) {
      // `group` porte lui-même data-tj-pill-group : le <p data-tj-pill-error>
      // est un frère (pas un descendant), donc on cherche dans le parent.
      const scope = group.parentElement;
      const errorEl = scope ? scope.querySelector("[data-tj-pill-error]") : null;
      if (errorEl) errorEl.classList.toggle("hidden", !show);
    }

    function stepIsValid(n) {
      const stepEl = steps.find((s) => parseInt(s.getAttribute("data-tj-step"), 10) === n);
      if (!stepEl) return true;

      const invalid = Array.from(stepEl.querySelectorAll("input, select, textarea")).find((el) => {
        if (el.disabled) return false;
        if (!el.willValidate) return false;
        return !el.checkValidity();
      });
      if (invalid) {
        invalid.reportValidity();
        return false;
      }

      const requireGroups = Array.from(stepEl.querySelectorAll("[data-tj-require-checked]"));
      for (const group of requireGroups) {
        const checkedCount = group.querySelectorAll("input:checked").length;
        showPillError(group, checkedCount === 0);
        if (checkedCount === 0) {
          group.scrollIntoView({ behavior: "smooth", block: "center" });
          return false;
        }
      }

      return true;
    }

    root.querySelectorAll("[data-tj-next]").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (!stepIsValid(current)) return;
        current = Math.min(total, current + 1);
        render();
        // scroll tout en haut de la PAGE (pas juste vers le formulaire) : un
        // root.scrollIntoView() atterrit sous le header sticky et masque une
        // partie du contenu, ce qui donnait l'impression que rien ne bougeait.
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    });
    root.querySelectorAll("[data-tj-prev]").forEach((btn) => {
      btn.addEventListener("click", () => {
        current = Math.max(1, current - 1);
        render();
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    });

    render();
  }

  function initRecurrence(root) {
    const radios = Array.from(root.querySelectorAll('input[name="recurrence_type"]'));
    if (!radios.length) return;

    const weekdaysContainer = root.querySelector("#weekdays_container");
    const dateRangeContainer = root.querySelector("#daterange_container");
    const dateFinContainer = root.querySelector("#date_fin_container"); // ancien balisage (proposition_rayon / recherche)
    const dateDebutInput = root.querySelector('input[name="date_debut"]');
    const dateFinInput = root.querySelector('input[name="date_fin"]');
    const weekdayInputs = Array.from(root.querySelectorAll('input[name="tr_weekdays"]'));
    const calendarEl = root.querySelector("[data-tj-calendar]");
    const recapEl = root.querySelector("[data-tj-recap]");

    const selectedInput = root.querySelector("[data-tj-selected-input]");
    const excludedInput = root.querySelector("[data-tj-excluded-input]");
    const excludedPanel = root.querySelector("[data-tj-excluded-panel]");
    const excludedSummary = root.querySelector("[data-tj-excluded-summary]");
    const excludedCounter = root.querySelector("[data-tj-excluded-counter]");
    const excludedList = root.querySelector("[data-tj-excluded-list]");

    // Calendrier avancé (sélection libre + exclusions) : seulement si le
    // template fournit les deux champs cachés dédiés. Sinon, comportement
    // hérité : aperçu lecture-seule piloté par date_debut/date_fin.
    const advanced = !!(selectedInput && excludedInput && dateRangeContainer);

    let calYear = new Date().getFullYear();
    let calMonth = new Date().getMonth();
    let activeField = "debut";
    let selectedDates = []; // mode one_week (libre) — ISO triés
    let excludedDates = []; // modes weekly/biweekly — ISO

    function selectedRecurrence() {
      const checked = root.querySelector('input[name="recurrence_type"]:checked');
      return checked ? checked.value : null;
    }
    function selectedWeekdays() {
      return weekdayInputs.filter((i) => i.checked).map((i) => parseInt(i.value, 10));
    }
    function setWeekdayChecks(days) {
      const set = new Set(days);
      weekdayInputs.forEach((i) => { i.checked = set.has(parseInt(i.value, 10)); });
    }
    function syncHiddenInputs() {
      if (selectedInput) selectedInput.value = selectedDates.join(",");
      if (excludedInput) excludedInput.value = excludedDates.join(",");
    }
    function jumpToIso(iso) {
      const d = parseIso(iso);
      if (d) { calYear = d.getFullYear(); calMonth = d.getMonth(); }
    }

    function updateVisibility() {
      const type = selectedRecurrence();
      const isRecurring = type === "weekly" || type === "biweekly";

      if (advanced) {
        if (weekdaysContainer) weekdaysContainer.classList.toggle("hidden", !isRecurring);
        if (dateRangeContainer) dateRangeContainer.classList.toggle("hidden", !isRecurring);
      } else {
        const daysCount = selectedWeekdays().length;
        if (weekdaysContainer) weekdaysContainer.classList.toggle("hidden", !isRecurring);
        if (dateFinContainer) {
          let show = isRecurring;
          if (type === "one_week") show = daysCount > 1;
          dateFinContainer.classList.toggle("hidden", !show);
        }
      }
    }

    function updateActiveFieldStyles() {
      if (!dateDebutInput || !dateFinInput) return;
      dateDebutInput.style.borderColor = activeField === "debut" ? BRAND : "";
      dateDebutInput.style.borderWidth = activeField === "debut" ? "2px" : "";
      dateFinInput.style.borderColor = activeField === "fin" ? BRAND : "";
      dateFinInput.style.borderWidth = activeField === "fin" ? "2px" : "";
    }

    function computeGenerated() {
      const type = selectedRecurrence();
      if (advanced && type === "one_week") {
        return selectedDates.map(parseIso).filter(Boolean);
      }
      const days = selectedWeekdays();
      const dateDebut = dateDebutInput ? parseIso(dateDebutInput.value) : null;
      const dateFin = dateFinInput ? parseIso(dateFinInput.value) : null;
      if (!type || !dateDebut) return [];
      return computeDates(type, days, dateDebut, dateFin);
    }

    function resetOnModeChange() {
      selectedDates = [];
      excludedDates = [];
      activeField = "debut";
      setWeekdayChecks([]);
      if (dateDebutInput) dateDebutInput.value = "";
      if (dateFinInput) dateFinInput.value = "";
      syncHiddenInputs();
      updateActiveFieldStyles();
    }

    // ── Mode "once" (one_week) : clic direct = ajoute/retire la date ──────
    function clickDayOnce(iso) {
      const idx = selectedDates.indexOf(iso);
      if (idx >= 0) selectedDates.splice(idx, 1); else selectedDates.push(iso);
      selectedDates.sort();

      // tr_weekdays / date_debut / date_fin restent requis côté serveur ;
      // on les dérive silencieusement de la sélection libre (champs masqués).
      if (selectedDates.length) {
        const days = selectedDates.map((d) => { const dt = parseIso(d); return dt.getDay() === 0 ? 7 : dt.getDay(); });
        setWeekdayChecks(days);
        if (dateDebutInput) dateDebutInput.value = selectedDates[0];
        if (dateFinInput) dateFinInput.value = selectedDates[selectedDates.length - 1];
      } else {
        setWeekdayChecks([]);
        if (dateDebutInput) dateDebutInput.value = "";
        if (dateFinInput) dateFinInput.value = "";
      }
      syncHiddenInputs();
      renderCalendar();
    }

    // ── Modes weekly/biweekly : clic = pose le début, puis la fin ──────────
    function clickDayRange(iso) {
      const db = dateDebutInput ? dateDebutInput.value : "";
      const df = dateFinInput ? dateFinInput.value : "";

      if (activeField === "fin") {
        if (db && iso < db) {
          if (dateDebutInput) dateDebutInput.value = iso;
          if (dateFinInput) dateFinInput.value = "";
          activeField = "fin";
        } else {
          if (dateFinInput) dateFinInput.value = iso;
          activeField = "debut";
        }
      } else {
        if (dateDebutInput) dateDebutInput.value = iso;
        if (dateFinInput) dateFinInput.value = (df && iso <= df) ? df : "";
        activeField = "fin";
      }

      updateActiveFieldStyles();
      renderCalendar();
    }

    function toggleExcluded(iso) {
      const idx = excludedDates.indexOf(iso);
      if (idx >= 0) excludedDates.splice(idx, 1); else excludedDates.push(iso);
      syncHiddenInputs();
      renderCalendar();
    }

    function renderRecap(generated) {
      if (!recapEl) return;
      const type = selectedRecurrence();
      if (!(advanced && type === "one_week") || !generated.length) {
        recapEl.classList.add("hidden");
        return;
      }
      recapEl.classList.remove("hidden");
      const labels = generated.map(fmtDate);
      let text;
      if (labels.length === 1) text = `1 trajet sera créé : ${labels[0]}`;
      else if (labels.length <= 5) text = `${labels.length} trajets seront créés : ${labels.join(" · ")}`;
      else text = `${labels.length} trajets seront créés : ${labels.slice(0, 5).join(" · ")} … et ${labels.length - 5} autre(s)`;
      recapEl.textContent = text;
    }

    function renderExcludedPanel(generated) {
      if (!excludedPanel) return;
      const type = selectedRecurrence();
      const isRecurring = type === "weekly" || type === "biweekly";
      if (!advanced || !isRecurring || !generated.length) {
        excludedPanel.classList.add("hidden");
        return;
      }
      excludedPanel.classList.remove("hidden");

      const excludedSet = new Set(excludedDates);
      const includedCount = generated.filter((d) => !excludedSet.has(isoOf(d))).length;
      const totalCount = generated.length;

      if (excludedSummary) excludedSummary.textContent = `${includedCount} trajet(s) seront créés`;
      if (excludedCounter) excludedCounter.textContent = `${includedCount} / ${totalCount} dates retenues`;

      if (excludedList) {
        excludedList.innerHTML = generated.map((d) => {
          const iso = isoOf(d);
          const excluded = excludedSet.has(iso);
          const label = fmtDate(d);
          const rowStyle = `display:inline-flex;align-items:center;gap:5px;padding:5px 6px 5px 12px;border-radius:20px;background:${excluded ? "#F9FAFB" : "#fff"};border:1px solid ${excluded ? "#E5E7EB" : "#B4D9D5"};`;
          const textStyle = `font-size:13px;font-weight:600;color:${excluded ? "#C0BFBA" : "#1C1C1C"};text-decoration:${excluded ? "line-through" : "none"};`;
          const btnStyle = `width:19px;height:19px;display:flex;align-items:center;justify-content:center;border-radius:50%;border:none;cursor:pointer;font-size:12px;line-height:1;font-weight:700;background:${excluded ? "#B4D9D5" : "#F0EFEA"};color:${excluded ? "#005A52" : "#9CA3AF"};`;
          return `<div style="${rowStyle}"><span style="${textStyle}">${label}</span><button type="button" data-tj-excl-toggle="${iso}" style="${btnStyle}">${excluded ? "↺" : "✕"}</button></div>`;
        }).join("");
        excludedList.querySelectorAll("[data-tj-excl-toggle]").forEach((btn) => {
          btn.addEventListener("click", () => toggleExcluded(btn.getAttribute("data-tj-excl-toggle")));
        });
      }
    }

    function renderCalendar() {
      if (!calendarEl) return;
      const type = selectedRecurrence();
      const generated = computeGenerated();
      const genSet = new Set(generated.map(isoOf));
      const selectedSet = new Set(selectedDates);
      const db = dateDebutInput ? dateDebutInput.value : "";
      const df = dateFinInput ? dateFinInput.value : "";

      const firstDow = new Date(calYear, calMonth, 1).getDay();
      const offset = firstDow === 0 ? 6 : firstDow - 1;
      const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
      const cells = [];
      for (let i = 0; i < offset; i++) cells.push(null);
      for (let d = 1; d <= daysInMonth; d++) cells.push(d);
      while (cells.length % 7 !== 0) cells.push(null);

      const today = new Date();
      const isToday = (d) => d && d === today.getDate() && calMonth === today.getMonth() && calYear === today.getFullYear();

      const navBtnStyle = "width:30px;height:30px;border-radius:8px;border:1.5px solid #E5E7EB;background:#fff;color:#6B7280;display:flex;align-items:center;justify-content:center;font-size:14px;cursor:pointer;flex-shrink:0;";

      let html = "";
      html += `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">`;
      html += `<button type="button" data-tj-cal-prev style="${navBtnStyle}">←</button>`;
      html += `<span style="font-weight:700;font-size:15px;color:#1C1C1C;">${MONTHS_FULL_FR[calMonth]} ${calYear}</span>`;
      html += `<button type="button" data-tj-cal-next style="${navBtnStyle}">→</button>`;
      html += `</div>`;

      html += `<div style="display:grid;grid-template-columns:repeat(7,1fr);margin-bottom:4px;">`;
      ["L", "M", "M", "J", "V", "S", "D"].forEach((x) => {
        html += `<div style="text-align:center;font-size:11px;font-weight:700;color:#BABAB5;letter-spacing:0.05em;padding-bottom:4px;">${x}</div>`;
      });
      html += `</div>`;

      const canClick = advanced && !!type;

      html += `<div style="display:grid;grid-template-columns:repeat(7,1fr);row-gap:2px;">`;
      cells.forEach((d) => {
        if (!d) { html += `<div></div>`; return; }
        const iso = `${calYear}-${pad2(calMonth + 1)}-${pad2(d)}`;
        let cellStyle = "text-align:center;border-radius:8px;font-size:14px;padding:6px 2px;";
        cellStyle += canClick ? "cursor:pointer;" : "";

        if (advanced && type === "one_week") {
          const sel = selectedSet.has(iso);
          const td = isToday(d) && !sel;
          if (sel) cellStyle += `background:${BRAND};color:#fff;font-weight:700;`;
          else if (td) cellStyle += `border:1.5px solid ${BRAND};color:${BRAND};font-weight:700;`;
          else cellStyle += "color:#1C1C1C;font-weight:400;";
        } else {
          const hl = !!type && genSet.has(iso);
          const inRange = !hl && !!db && !!df && iso > db && iso < df;
          const isStart = !hl && !!db && iso === db;
          const isEnd = !hl && !!df && df !== db && iso === df;
          const td = isToday(d) && !hl && !isStart && !isEnd;

          if (hl) cellStyle += `background:${BRAND};color:#fff;font-weight:700;`;
          else if (isStart || isEnd) cellStyle += `background:${BRAND_MID};color:#fff;font-weight:700;`;
          else if (inRange) cellStyle += `background:${BRAND_LIGHT};color:#1C1C1C;font-weight:400;`;
          else cellStyle += "color:#1C1C1C;font-weight:400;";

          if (td) cellStyle += `border:1.5px solid ${BRAND};color:${BRAND};font-weight:700;`;
        }

        html += `<div class="tj-cal-cell" data-tj-cal-day="${iso}" style="${cellStyle}">${d}</div>`;
      });
      html += `</div>`;

      calendarEl.innerHTML = html;

      const prevBtn = calendarEl.querySelector("[data-tj-cal-prev]");
      const nextBtn = calendarEl.querySelector("[data-tj-cal-next]");
      if (prevBtn) prevBtn.addEventListener("click", () => { calMonth--; if (calMonth < 0) { calMonth = 11; calYear--; } renderCalendar(); });
      if (nextBtn) nextBtn.addEventListener("click", () => { calMonth++; if (calMonth > 11) { calMonth = 0; calYear++; } renderCalendar(); });

      if (canClick) {
        calendarEl.querySelectorAll("[data-tj-cal-day]").forEach((cell) => {
          cell.addEventListener("click", () => {
            const iso = cell.getAttribute("data-tj-cal-day");
            if (type === "one_week") clickDayOnce(iso);
            else clickDayRange(iso);
          });
        });
      }

      renderRecap(generated);
      renderExcludedPanel(generated);
    }

    radios.forEach((r) => r.addEventListener("change", () => {
      if (advanced) resetOnModeChange();
      updateVisibility();
      renderCalendar();
    }));
    weekdayInputs.forEach((i) => i.addEventListener("change", () => { updateVisibility(); renderCalendar(); }));
    if (dateDebutInput) {
      dateDebutInput.addEventListener("focus", () => { if (advanced) { activeField = "debut"; updateActiveFieldStyles(); } });
      dateDebutInput.addEventListener("change", () => { jumpToIso(dateDebutInput.value); renderCalendar(); });
    }
    if (dateFinInput) {
      dateFinInput.addEventListener("focus", () => { if (advanced) { activeField = "fin"; updateActiveFieldStyles(); } });
      dateFinInput.addEventListener("change", renderCalendar);
    }

    // État initial : si une date de début existe déjà (réaffichage après erreur),
    // on centre le calendrier dessus.
    if (dateDebutInput && dateDebutInput.value) jumpToIso(dateDebutInput.value);

    updateVisibility();
    updateActiveFieldStyles();
    renderCalendar();
  }

  function initRadiusSlider(root) {
    const slider = root.querySelector('input[name="search_radius_km"]');
    const label = root.querySelector("[data-tj-radius-label]");
    const track = root.querySelector("[data-tj-radius-track]");
    if (!slider) return;

    function refresh() {
      const min = parseFloat(slider.min || "1");
      const max = parseFloat(slider.max || "50");
      const val = parseFloat(slider.value || String(min));
      if (label) label.textContent = `${val} km`;
      if (track) {
        const pct = ((val - min) / (max - min)) * 100;
        track.style.width = `${pct}%`;
      }
    }
    slider.addEventListener("input", refresh);
    refresh();
  }

  function initAll() {
    document.querySelectorAll("[data-tj-wizard]").forEach((root) => {
      initWizard(root);
      initRecurrence(root);
      initRadiusSlider(root);

      const weekdaySelector = root.querySelector("#weekday-selector");
      if (weekdaySelector) {
        initPillGroup(weekdaySelector, DAY_PILL_ACTIVE, DAY_PILL_INACTIVE);
      }

      root.querySelectorAll("[data-tj-pill-group]").forEach((group) => {
        initPillGroup(group, PILL_ACTIVE, PILL_INACTIVE);
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
