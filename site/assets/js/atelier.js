/**
 * Atelier : transforme le JSON rédigé par un assistant IA en fichiers (plan, support, quiz) en
 * exécutant dans le navigateur, avec Pyodide, les mêmes scripts Python que les skills.
 */
const PYODIDE = 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs';

const TYPES = {
  plan: {
    skill: 'skazy-plan-formation',
    libelle: 'Plan de formation',
    formats: [
      ['html', 'HTML (A4, à imprimer en PDF)'],
      ['docx', 'DOCX (Word, Google Docs)'],
    ],
    paquets: ['micropip', 'lxml', 'pillow'],
    pip: ['python-docx'],
  },
  support: {
    skill: 'skazy-support-formation',
    libelle: 'Support de formation',
    formats: [
      ['html', 'HTML (diaporama, PDF)'],
      ['pptx', 'PPTX (PowerPoint, Google Slides)'],
    ],
    paquets: ['micropip', 'lxml', 'pillow'],
    pip: ['python-pptx'],
  },
  quiz: {
    skill: 'skazy-quiz',
    libelle: 'Quiz',
    formats: [
      ['skazy', 'Quiz Skazy (JSON et lien)'],
      ['kahoot', 'Kahoot (.xlsx)'],
      ['forms', 'Google Forms (script)'],
      ['corrige', 'Corrigé (.md)'],
    ],
    paquets: ['micropip'],
    pip: ['openpyxl'],
  },
};

const TYPES_MIME = {
  html: 'text/html',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  pptx: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  json: 'application/json',
  gs: 'text/plain',
  md: 'text/markdown',
  txt: 'text/plain',
};

// Code Python exécuté dans Pyodide : mêmes fonctions que les scripts en ligne de commande.
const PYTHON = {
  plan: `
import base64, json, sys
sys.path.insert(0, "/skills/skazy-plan-formation/scripts")
import charte as ch, rendre_plan as r
p, rapport = r.normaliser_plan(json.loads(TEXTE))
fichiers = {}
if rapport.ok:
    base = "plan-" + ch.slug(p["intitule"])
    if "html" in FORMATS:
        fichiers[base + ".html"] = r.rendre_html(p).encode("utf-8")
    if "docx" in FORMATS:
        fichiers[base + ".docx"] = r.rendre_docx(p)
json.dumps({"erreurs": rapport.erreurs, "avertissements": rapport.avertissements, "lien": None,
            "fichiers": {k: base64.b64encode(v).decode() for k, v in fichiers.items()}})
`,
  supportImages: `
import json, sys
sys.path.insert(0, "/skills/skazy-support-formation/scripts")
import charte as ch, support_modele as m
s, rapport = m.normaliser_support(json.loads(TEXTE))
urls = []
if rapport.ok and "pptx" in FORMATS:
    import support_pptx
    urls = support_pptx.urls_images(s)
json.dumps(urls)
`,
  support: `
import base64, json, sys
sys.path.insert(0, "/skills/skazy-support-formation/scripts")
import charte as ch, support_modele as m
images = IMAGES.to_py() if hasattr(IMAGES, "to_py") else IMAGES
for url, donnees in images.items():
    ch.IMAGES_LOCALES[url] = bytes(donnees.to_py() if hasattr(donnees, "to_py") else donnees)
s, rapport = m.normaliser_support(json.loads(TEXTE))
fichiers = {}
if rapport.ok:
    base = "support-" + ch.slug(s["formation"]["intitule"])
    if "html" in FORMATS:
        from support_html import rendre_html
        fichiers[base + ".html"] = rendre_html(s).encode("utf-8")
    if "pptx" in FORMATS:
        from support_pptx import rendre_pptx
        fichiers[base + ".pptx"] = rendre_pptx(s)
json.dumps({"erreurs": rapport.erreurs, "avertissements": rapport.avertissements, "lien": None,
            "fichiers": {k: base64.b64encode(v).decode() for k, v in fichiers.items()}})
`,
  quiz: `
import base64, json, sys
sys.path.insert(0, "/skills/skazy-quiz/scripts")
import charte as ch, rendre_quiz as rq
q, rapport = rq.normaliser_quiz(json.loads(TEXTE))
fichiers, lien = {}, None
if rapport.ok:
    base = "quiz-" + ch.slug(q["title"])
    lien = rq.lien_partage(q)
    if "skazy" in FORMATS:
        fichiers[base + ".skazy-quiz.json"] = json.dumps(rq.export_skazy(q), ensure_ascii=False, indent=2).encode("utf-8")
    if "kahoot" in FORMATS:
        fichiers[base + ".kahoot.xlsx"] = rq.export_kahoot(q, rapport)
    if "forms" in FORMATS:
        fichiers[base + ".google-forms.gs"] = rq.export_forms(q, rapport).encode("utf-8")
    if "corrige" in FORMATS:
        fichiers[base + ".corrige.md"] = rq.export_corrige(q).encode("utf-8")
json.dumps({"erreurs": rapport.erreurs, "avertissements": rapport.avertissements, "lien": lien,
            "fichiers": {k: base64.b64encode(v).decode() for k, v in fichiers.items()}})
`,
};

const $ = (id) => document.getElementById(id);
const entree = $('entree');
const etat = $('etat');
const liste = $('fichiers');
const rapport = $('rapport');
const bouton = $('produire');
let pyodide = null;
let typeCourant = null;
const installes = new Set();
const charges = new Set();
const liensObjets = [];

function lireJson() {
  try {
    return JSON.parse(entree.value);
  } catch {
    return null;
  }
}

function detecter(objet) {
  if (!objet || typeof objet !== 'object') return null;
  const format = objet.format ?? objet.quiz?.format;
  if (format === 'skazy-plan' || objet.programme) return 'plan';
  if (format === 'skazy-support' || objet.slides) return 'support';
  if (format === 'skazy-quiz' || objet.quiz || objet.questions) return 'quiz';
  return null;
}

function majFormats() {
  const type = detecter(lireJson());
  if (type === typeCourant) return;
  typeCourant = type;
  const bloc = $('formats');
  if (!type) {
    bloc.hidden = true;
    return;
  }
  $('cases').replaceChildren(
    ...TYPES[type].formats.map(([valeur, libelle]) => {
      const label = document.createElement('label');
      label.innerHTML = `<input type="checkbox" name="format" value="${valeur}" checked> ${libelle}`;
      return label;
    }),
  );
  bloc.querySelector('legend').textContent = `${TYPES[type].libelle} : fichiers à produire`;
  bloc.hidden = false;
}

function dire(message) {
  etat.textContent = message;
}

async function preparer(type) {
  const t = TYPES[type];
  if (!pyodide) {
    dire('Chargement du moteur Python (Pyodide)…');
    const { loadPyodide } = await import(PYODIDE);
    pyodide = await loadPyodide();
  }
  const paquets = t.paquets.filter((p) => !installes.has(p));
  if (paquets.length) {
    dire('Chargement des bibliothèques (' + paquets.join(', ') + ')…');
    await pyodide.loadPackage(paquets);
    paquets.forEach((p) => installes.add(p));
  }
  const pip = t.pip.filter((p) => !installes.has(p));
  if (pip.length) {
    dire('Installation de ' + pip.join(', ') + '…');
    const micropip = pyodide.pyimport('micropip');
    await micropip.install(pip);
    pip.forEach((p) => installes.add(p));
  }
  if (!charges.has(t.skill)) {
    dire('Chargement des scripts du skill ' + t.skill + '…');
    const index = await (await fetch('../sources/index.json')).json();
    const fichiers = index[t.skill].filter(
      (f) => f.startsWith('scripts/') || f.startsWith('assets/'),
    );
    await Promise.all(
      fichiers.map(async (f) => {
        const reponse = await fetch(`../sources/${t.skill}/${f}`);
        if (!reponse.ok) throw new Error(`Fichier introuvable : ${f}`);
        const chemin = `/skills/${t.skill}/${f}`;
        pyodide.FS.mkdirTree(chemin.slice(0, chemin.lastIndexOf('/')));
        pyodide.FS.writeFile(chemin, new Uint8Array(await reponse.arrayBuffer()));
      }),
    );
    charges.add(t.skill);
  }
}

async function telechargerImages(urls) {
  const images = {};
  let n = 0;
  for (const url of urls) {
    dire(`Téléchargement des photos (${++n}/${urls.length})…`);
    try {
      const reponse = await fetch(url);
      if (reponse.ok) images[url] = new Uint8Array(await reponse.arrayBuffer());
    } catch {
      // photo indisponible : le PPTX garde un emplacement à remplir
    }
  }
  return images;
}

function decoder(base64) {
  const binaire = atob(base64);
  return Uint8Array.from(binaire, (c) => c.charCodeAt(0));
}

function afficher(resultat) {
  liensObjets.splice(0).forEach((u) => URL.revokeObjectURL(u));
  liste.replaceChildren();
  rapport.replaceChildren();
  const ligne = (classe, texte) => {
    const p = document.createElement('p');
    p.className = classe;
    p.textContent = texte;
    rapport.append(p);
  };
  resultat.erreurs.forEach((m) => ligne('erreur', 'Erreur : ' + m));
  resultat.avertissements.forEach((m) => ligne('attention', 'Attention : ' + m));
  for (const [nom, contenu] of Object.entries(resultat.fichiers)) {
    const extension = nom.split('.').pop();
    const url = URL.createObjectURL(
      new Blob([decoder(contenu)], { type: TYPES_MIME[extension] ?? 'application/octet-stream' }),
    );
    liensObjets.push(url);
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.className = 'bouton bouton--primaire';
    a.href = url;
    a.download = nom;
    a.innerHTML = '<svg class="icone" aria-hidden="true"><use href="#i-download"></use></svg>';
    a.append(nom);
    li.append(a);
    if (extension === 'html') {
      const apercu = document.createElement('a');
      apercu.href = url;
      apercu.target = '_blank';
      apercu.rel = 'noopener';
      apercu.textContent = 'Aperçu';
      li.append(apercu);
    }
    liste.append(li);
  }
  if (resultat.lien) {
    const li = document.createElement('li');
    li.innerHTML =
      '<a class="bouton bouton--secondaire" target="_blank" rel="noopener"><svg class="icone" aria-hidden="true"><use href="#i-external-link"></use></svg>Ouvrir dans le Quiz</a>';
    li.querySelector('a').href = resultat.lien;
    const copie = document.createElement('button');
    copie.type = 'button';
    copie.className = 'lien';
    copie.textContent = 'Copier le lien';
    copie.addEventListener('click', async () => {
      await navigator.clipboard.writeText(resultat.lien);
      copie.textContent = 'Lien copié';
    });
    li.append(copie);
    liste.append(li);
  }
  if (!resultat.erreurs.length)
    ligne('ok', `${Object.keys(resultat.fichiers).length} fichier(s) prêt(s).`);
}

async function produire(evenement) {
  evenement.preventDefault();
  const objet = lireJson();
  if (!objet) {
    dire(
      'Le texte collé n’est pas un JSON valide : vérifiez qu’il est complet (accolades, guillemets).',
    );
    return;
  }
  const type = detecter(objet);
  if (!type) {
    dire(
      'Type de document non reconnu : le JSON doit contenir « format » (skazy-plan, skazy-support ou skazy-quiz).',
    );
    return;
  }
  const formats = [...document.querySelectorAll('input[name="format"]:checked')].map(
    (c) => c.value,
  );
  if (!formats.length) {
    dire('Cochez au moins un fichier à produire.');
    return;
  }
  bouton.setAttribute('aria-busy', 'true');
  bouton.disabled = true;
  try {
    await preparer(type);
    pyodide.globals.set('TEXTE', entree.value);
    pyodide.globals.set('FORMATS', pyodide.toPy(formats));
    let code = PYTHON[type];
    if (type === 'support') {
      const urls = JSON.parse(await pyodide.runPythonAsync(PYTHON.supportImages));
      pyodide.globals.set('IMAGES', pyodide.toPy(await telechargerImages(urls)));
      code = PYTHON.support;
    }
    dire('Production des fichiers…');
    const resultat = JSON.parse(await pyodide.runPythonAsync(code));
    afficher(resultat);
    dire(
      resultat.erreurs.length
        ? 'Le JSON contient des erreurs : corrigez-les puis relancez.'
        : 'Fichiers prêts.',
    );
  } catch (erreur) {
    console.error(erreur);
    dire(
      'La production a échoué : ' +
        (erreur.message ?? erreur).toString().split('\n').slice(-2).join(' '),
    );
  } finally {
    bouton.removeAttribute('aria-busy');
    bouton.disabled = false;
  }
}

entree.addEventListener('input', majFormats);
$('fichier').addEventListener('change', async (e) => {
  const fichier = e.target.files[0];
  if (!fichier) return;
  entree.value = await fichier.text();
  majFormats();
});
for (const b of document.querySelectorAll('[data-exemple]')) {
  b.addEventListener('click', async () => {
    entree.value = await (await fetch(`../sources/${b.dataset.exemple}`)).text();
    majFormats();
    entree.focus();
  });
}
$('formulaire').addEventListener('submit', produire);
