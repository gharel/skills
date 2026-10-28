/* Généré par design-skazy (npm run charte) depuis
   templates/plan-formation/PlanFormation.dc.html : ne pas modifier.
   Ajustements du modèle : taille des titres (data-fit), densité du programme et pages de suite,
   page des informations resserrée. Appel : SkazyPlanFormation.ajuster(élément qui contient les pages). */
(() => {
class Component {
  static MAX_DENSITY = 4;
  fitText(el) {
    if (!el.getClientRects().length) return;
    const [max, max2, min] = el.getAttribute('data-fit').split(',').map(Number);
    for (let s = max; s >= min; s--) {
      el.style.fontSize = s + 'px';
      const lh = parseFloat(getComputedStyle(el).lineHeight) || s * 1.1;
      const lines = Math.round(el.getBoundingClientRect().height / lh);
      const wide = el.scrollWidth > el.clientWidth + 1;
      if (!wide && (lines <= 1 || (lines === 2 && s <= max2))) break;
    }
  }
  fitTitles(root) {
    root.querySelectorAll('[data-fit]').forEach((el) => this.fitText(el));
  }
  fitInfo(root) {
    const info = root.querySelector('[data-info]');
    if (!info) return;
    info.removeAttribute('data-tight');
    if (info.scrollHeight > info.clientHeight + 1) info.setAttribute('data-tight', '');
    if (info.scrollHeight > info.clientHeight + 1) console.warn('[plan-formation] la page des informations déborde');
  }
  paginate(root) {
    const prog = root.querySelector('[data-prog]');
    if (!prog) return;
    const page1 = prog.closest('.page');
    const progH = page1.querySelector('[data-prog-h]');
    const foot = page1.querySelector('[data-pfoot]');
    const title = (root.querySelector('.pf-h1') || {}).textContent || '';

    // 1. Remet tout à sa place d'origine et retire les pages de suite
    root.querySelectorAll('[data-gen]').forEach((g) => {
      g.querySelectorAll('.pf-part').forEach((p) => { if (p.__box && p.__box.isConnected) p.__box.appendChild(p); });
      g.remove();
    });
    const parts = [];
    prog.querySelectorAll(':scope > .pf-day').forEach((day) => {
      day.querySelectorAll(':scope > .pf-parts > .pf-part').forEach((p) => { p.__day = day; p.__box = p.parentNode; parts.push(p); });
    });

    const limitOf = (pg) => {
      const r = pg.getBoundingClientRect();
      return r.top + r.height - (pg.querySelector('[data-pfoot]') || { offsetHeight: 0 }).offsetHeight - 18;
    };
    const lim1 = limitOf(page1);
    let gens = [];

    // 2. Répartition pour une densité donnée : retourne { pages, p1 } (p1 = parties sur la page 1)
    const flow = (d) => {
      gens.forEach((g) => g.remove());
      gens = [];
      parts.forEach((p) => p.remove());
      prog.setAttribute('data-density', d);
      let i = 0;
      while (i < parts.length) {
        parts[i].__box.appendChild(parts[i]);
        if (prog.getBoundingClientRect().bottom > lim1 + 0.5) { parts[i].remove(); break; }
        i++;
      }
      const p1 = i;
      const seen = new Set(parts.slice(0, i).map((p) => p.__day));
      while (i < parts.length) {
        const g = this.makeGenPage(title, foot, d);
        (gens.length ? gens[gens.length - 1] : page1).after(g);
        gens.push(g);
        const gp = g.querySelector('[data-prog-gen]');
        const lim = limitOf(g);
        let placed = 0;
        while (i < parts.length) {
          const p = parts[i];
          let w = gp.lastElementChild;
          if (!w || w.__day !== p.__day) {
            w = this.makeGenDay(p.__day, seen.has(p.__day));
            gp.appendChild(w);
          }
          w.lastElementChild.appendChild(p);
          if (placed > 0 && gp.getBoundingClientRect().bottom > lim + 0.5) {
            p.remove();
            if (!w.lastElementChild.children.length) w.remove();
            break;
          }
          seen.add(p.__day);
          placed++; i++;
        }
      }
      return { pages: 1 + gens.length, p1 };
    };

    // 3. Densité la plus aérée donnant le plus petit nombre de pages
    let best = null, last = null;
    for (let d = 0; d <= Component.MAX_DENSITY; d++) {
      last = { d, ...flow(d) };
      if (!best || last.pages < best.pages) best = last;
      if (last.pages === 1) break;
    }
    if (last.d !== best.d) last = { d: best.d, ...flow(best.d) };
    if (progH) { if (last.p1 === 0) progH.setAttribute('data-off', ''); else progH.removeAttribute('data-off'); }
    this._prog = { density: last.d, pages: last.pages };
    prog.setAttribute('data-pages', last.pages);
  }
  makeGenPage(title, foot, d) {
    const s = document.createElement('section');
    s.className = 'page pf-page';
    s.setAttribute('data-gen', '');
    s.setAttribute('data-screen-label', 'Programme (suite)');
    s.innerHTML = '<div class="pf-strip"><span class="pf-strip-t" data-fit="20,19,19"></span><span class="pf-pill">Programme (suite)</span></div>' +
      '<div class="pf-body pf-body--more"><div class="pf-prog" data-prog-gen="" data-density="' + d + '"></div></div>';
    s.querySelector('.pf-strip-t').textContent = title.trim();
    if (foot) s.querySelector('.pf-body').appendChild(foot.cloneNode(true));
    return s;
  }
  makeGenDay(day, again) {
    const w = document.createElement('section');
    w.className = 'pf-day';
    w.__day = day;
    const h = day.querySelector(':scope > .pf-dayh');
    if (h) {
      const c = h.cloneNode(true);
      if (again) { const m = document.createElement('span'); m.className = 'pf-dayc'; m.textContent = '(suite)'; c.appendChild(m); }
      w.appendChild(c);
    }
    const box = document.createElement('div');
    box.className = 'pf-parts';
    w.appendChild(box);
    return w;
  }
}
const plan = new Component();
window.SkazyPlanFormation = {
  ajuster(racine = document) {
    plan.paginate(racine);
    plan.fitTitles(racine);
    plan.fitInfo(racine);
    return plan._prog;
  },
};
})();
