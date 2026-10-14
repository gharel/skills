/**
 * Bouton du thème : celui du système, clair, puis sombre. Le choix est gardé dans le navigateur
 * (clé « skazy-outils:theme ») ; le script en ligne du <head> l'applique avant l'affichage.
 * Les six outils partagent cette clé (même origine) : un choix fait dans l'un vaut pour tous, et
 * la page le suit aussitôt (autre onglet, ou retour en arrière depuis un outil).
 */
const CLE = 'skazy-outils:theme';

const THEMES = {
  auto: { suivant: 'light', icone: 'circle-half-stroke', nom: 'Thème : celui du système' },
  light: { suivant: 'dark', icone: 'sun', nom: 'Thème : clair' },
  dark: { suivant: 'auto', icone: 'moon', nom: 'Thème : sombre' },
};

// Couleur de la barre du navigateur sur téléphone : celle du bandeau.
const BARRE = { light: '#ffffff', dark: '#1f1f1f' };

function lire() {
  try {
    const theme = JSON.parse(localStorage.getItem(CLE));
    return theme === 'light' || theme === 'dark' ? theme : 'auto';
  } catch {
    return 'auto';
  }
}

function ecrire(theme) {
  try {
    if (theme === 'auto') localStorage.removeItem(CLE);
    else localStorage.setItem(CLE, JSON.stringify(theme));
  } catch {
    // stockage indisponible : le choix vaut pour cette visite
  }
}

const bouton = document.getElementById('bouton-theme');
const usage = bouton.querySelector('use');
const barres = document.querySelectorAll('meta[name="theme-color"]');

function appliquer(theme) {
  if (theme === 'auto') delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = theme;
  for (const meta of barres) {
    const schema = meta.media.includes('dark') ? 'dark' : 'light';
    meta.content = BARRE[theme === 'auto' ? schema : theme];
  }
  const t = THEMES[theme];
  usage.setAttribute('href', `#i-${t.icone}`);
  // Espace insécable avant les deux-points, comme dans tout le texte de la page.
  const nom = `${t.nom.replace(' :', ' :')}. Changer de thème`;
  bouton.setAttribute('aria-label', nom);
  bouton.title = nom;
}

let theme = lire();
appliquer(theme);
bouton.hidden = false;
bouton.addEventListener('click', () => {
  theme = THEMES[theme].suivant;
  ecrire(theme);
  appliquer(theme);
});

function resynchroniser() {
  theme = lire();
  appliquer(theme);
}

// Choix changé dans un autre onglet d'un outil (clé null : stockage vidé).
addEventListener('storage', (evenement) => {
  if (evenement.key === CLE || evenement.key === null) resynchroniser();
});

// Retour sur la page depuis le cache du navigateur (bfcache), après un détour par un outil.
addEventListener('pageshow', (evenement) => {
  if (evenement.persisted) resynchroniser();
});
