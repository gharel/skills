/**
 * Catalogue des skills : onglets d'installation, boutons « Copier » et repérage des nouvelles
 * versions depuis la dernière visite (versions vues gardées dans le navigateur).
 */
const CLE_VERSIONS = 'skazy-skills:versions';

// ── Onglets d'installation (sans JavaScript, tous les panneaux restent visibles) ──
for (const bloc of document.querySelectorAll('[data-onglets]')) {
  const liste = bloc.querySelector('[role="tablist"]');
  const onglets = [...liste.querySelectorAll('[role="tab"]')];
  const panneaux = onglets.map((o) => document.getElementById(o.getAttribute('aria-controls')));
  const choisir = (index, focus = false) => {
    onglets.forEach((o, k) => {
      const actif = k === index;
      o.setAttribute('aria-selected', String(actif));
      o.tabIndex = actif ? 0 : -1;
      panneaux[k].hidden = !actif;
    });
    if (focus) onglets[index].focus();
  };
  onglets.forEach((onglet, k) => {
    onglet.addEventListener('click', () => choisir(k));
    onglet.addEventListener('keydown', (e) => {
      const suivant = { ArrowRight: k + 1, ArrowLeft: k - 1, Home: 0, End: onglets.length - 1 }[
        e.key
      ];
      if (suivant === undefined) return;
      e.preventDefault();
      choisir((suivant + onglets.length) % onglets.length, true);
    });
  });
  panneaux.forEach((p) => p.setAttribute('tabindex', '0'));
  liste.hidden = false;
  bloc.classList.add('onglets--actifs');
  // Onglet ouvert par défaut selon l'appareil : ChatGPT ou Claude, les plus courants.
  choisir(0);
}

// ── Copier une commande ou des instructions ──
async function copier(texte, bouton) {
  try {
    await navigator.clipboard.writeText(texte);
    const libelle = bouton.textContent;
    bouton.textContent = 'Copié';
    setTimeout(() => (bouton.textContent = libelle), 1600);
  } catch {
    window.prompt('Copiez le texte :', texte);
  }
}
for (const bouton of document.querySelectorAll('[data-copier]')) {
  bouton.addEventListener('click', () => {
    const cible = bouton.dataset.copier
      ? document.getElementById(bouton.dataset.copier)
      : bouton.parentElement.querySelector('code');
    copier((cible.content ?? cible).textContent.trim(), bouton);
  });
}

// ── Nouvelles versions depuis la dernière visite ──
function lireVues() {
  try {
    return JSON.parse(localStorage.getItem(CLE_VERSIONS)) ?? {};
  } catch {
    return {};
  }
}
const vues = lireVues();
const actuelles = {};
for (const carte of document.querySelectorAll('.carte[data-skill]')) {
  const { skill, version } = carte.dataset;
  actuelles[skill] = version;
  if (vues[skill] && vues[skill] !== version) carte.querySelector('.badge--nouveau').hidden = false;
}
try {
  localStorage.setItem(CLE_VERSIONS, JSON.stringify({ ...vues, ...actuelles }));
} catch {
  // stockage indisponible : pas de repérage des nouveautés
}
