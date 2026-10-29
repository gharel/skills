/**
 * Bibliothèque commune des outils du dépôt : catégories, lecture et contrôle des skills.
 */
import { readFile, readdir, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, relative, dirname } from 'node:path';
import { parse as lireYaml } from 'yaml';
import { fileURLToPath } from 'node:url';

export const RACINE = fileURLToPath(new URL('../', import.meta.url));
export const DOSSIER_SKILLS = join(RACINE, 'skills');
export const DEPOT = 'gharel/skills';
export const URL_SITE = 'https://gharel.github.io/skills/';
export const URL_DEPOT = `https://github.com/${DEPOT}`;

/** Les trois catégories, dans l'ordre d'affichage du catalogue. */
export const CATEGORIES = [
  {
    id: 'pro',
    titre: 'Pro',
    sousTitre: 'Skazy Formation',
    description:
      'Concevoir et animer les formations Skazy Formation : plan, support et quiz, aux couleurs de la charte.',
    plugin: 'skazy-formation',
  },
  {
    id: 'unc',
    titre: 'UNC',
    sousTitre: 'Université de la Nouvelle-Calédonie',
    description: 'Cours, évaluations et suivi des étudiants.',
    plugin: 'unc',
  },
  {
    id: 'perso',
    titre: 'Perso',
    sousTitre: 'Usage personnel',
    description: 'Les skills du quotidien.',
    plugin: 'perso',
  },
];

/**
 * Statuts d'un skill (metadata.statut, inspirés de SkillCrew) : ce que font les installeurs.
 *   recommande : installé par défaut (statut sans metadata.statut) ;
 *   disponible : installé seulement si on le demande (SKILLS=<nom>) ;
 *   deprecie   : gardé là où il est déjà installé, plus installé ailleurs (metadata.remplace_par) ;
 *   retire     : absent du catalogue, supprimé des machines à la prochaine mise à jour.
 */
export const STATUTS = ['recommande', 'disponible', 'deprecie', 'retire'];

const NOM_VALIDE = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const VERSION_VALIDE = /^\d+\.\d+\.\d+$/;

/**
 * Lit l'en-tête YAML d'un SKILL.md (sous-ensemble utilisé ici : `clé: valeur` sur une ligne,
 * guillemets facultatifs, et un niveau d'imbrication pour `metadata`).
 */
export function lireFrontmatter(texte) {
  const m = texte.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (!m) return { donnees: null, corps: texte };
  const donnees = {};
  let parent = null;
  for (const ligne of m[1].split(/\r?\n/)) {
    if (!ligne.trim() || ligne.trim().startsWith('#')) continue;
    const imbrique = /^\s+/.test(ligne);
    const [, cle, valeur = ''] = ligne.trim().match(/^([A-Za-z0-9_-]+):\s*(.*)$/) ?? [];
    if (!cle) continue;
    const propre = valeur.replace(/^(["'])(.*)\1$/, '$2');
    if (imbrique && parent) donnees[parent][cle] = propre;
    else if (valeur === '') {
      parent = cle;
      donnees[cle] = {};
    } else {
      parent = null;
      donnees[cle] = propre;
    }
  }
  return { donnees, corps: texte.slice(m[0].length) };
}

/** Lit l'en-tête affichage de agents/openai.yaml (display_name, short_description). */
export function lireOpenai(texte) {
  const lire = (cle) => texte.match(new RegExp(`^\\s+${cle}:\\s*(.+)$`, 'm'))?.[1]?.trim() ?? '';
  return { titre: lire('display_name'), resume: lire('short_description') };
}

async function fichiersDe(dossier) {
  const liste = [];
  for (const entree of await readdir(dossier, { withFileTypes: true })) {
    const chemin = join(dossier, entree.name);
    if (entree.name === '__pycache__' || entree.name.startsWith('.')) continue;
    if (entree.isDirectory()) liste.push(...(await fichiersDe(chemin)));
    else liste.push(chemin);
  }
  return liste;
}

/** Tous les skills du dépôt : skills/<catégorie>/<nom>/SKILL.md (le dossier _modele est ignoré). */
export async function listerSkills() {
  const skills = [];
  for (const categorie of CATEGORIES) {
    const dossierCategorie = join(DOSSIER_SKILLS, categorie.id);
    if (!existsSync(dossierCategorie)) continue;
    for (const entree of await readdir(dossierCategorie, { withFileTypes: true })) {
      if (!entree.isDirectory() || entree.name.startsWith('_')) continue;
      const dossier = join(dossierCategorie, entree.name);
      const chemin = join(dossier, 'SKILL.md');
      if (!existsSync(chemin)) continue;
      const texte = await readFile(chemin, 'utf8');
      const { donnees, corps } = lireFrontmatter(texte);
      const openai = existsSync(join(dossier, 'agents/openai.yaml'))
        ? lireOpenai(await readFile(join(dossier, 'agents/openai.yaml'), 'utf8'))
        : { titre: '', resume: '' };
      const fichiers = (await fichiersDe(dossier)).map((f) =>
        relative(dossier, f).replaceAll('\\', '/'),
      );
      let taille = 0;
      for (const f of fichiers) taille += (await stat(join(dossier, f))).size;
      skills.push({
        dossier,
        chemin: relative(RACINE, dossier).replaceAll('\\', '/'),
        categorie: categorie.id,
        dossierNom: entree.name,
        texte,
        corps,
        donnees: donnees ?? {},
        nom: donnees?.name ?? '',
        description: donnees?.description ?? '',
        version: donnees?.metadata?.version ?? '',
        statut: donnees?.metadata?.statut || 'recommande',
        remplacePar: donnees?.metadata?.remplace_par ?? '',
        titre: openai.titre || donnees?.name || entree.name,
        resume: openai.resume || '',
        fichiers,
        taille,
      });
    }
  }
  // Ordre d'affichage : catégorie, puis metadata.ordre (la chaîne plan → support → quiz), puis nom.
  const rang = (s) => Number(s.donnees.metadata?.ordre ?? 99);
  const cat = (s) => CATEGORIES.findIndex((c) => c.id === s.categorie);
  return skills.sort((a, b) => cat(a) - cat(b) || rang(a) - rang(b) || a.nom.localeCompare(b.nom));
}

/** Contrôle d'un skill selon la spécification Agent Skills (agentskills.io) et les règles du dépôt. */
export function controler(skill) {
  const erreurs = [];
  const { donnees, nom, description, version } = skill;
  const ou = skill.chemin;
  if (!skill.texte.startsWith('---'))
    erreurs.push(`${ou} : SKILL.md doit commencer par un en-tête YAML (---).`);
  // L'en-tête doit être du YAML valide pour tous les outils (Claude.ai, ChatGPT, npx skills) :
  // un « : » dans une valeur sans guillemets le rend invalide.
  const entete = skill.texte.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (entete) {
    try {
      const yaml = lireYaml(entete[1]);
      if (yaml?.description !== description)
        erreurs.push(`${ou} : description mal lue (mettez-la entre guillemets, sur une ligne).`);
    } catch (e) {
      erreurs.push(
        `${ou} : en-tête YAML invalide (${e.message.split('\n')[0]}). Mettez les valeurs entre guillemets.`,
      );
    }
  }
  if (!nom) erreurs.push(`${ou} : champ « name » manquant.`);
  else {
    if (nom !== skill.dossierNom)
      erreurs.push(`${ou} : « name » (${nom}) doit être le nom du dossier.`);
    if (nom.length > 64 || !NOM_VALIDE.test(nom))
      erreurs.push(
        `${ou} : « name » : 64 caractères au plus, minuscules, chiffres et tirets simples.`,
      );
  }
  if (!description) erreurs.push(`${ou} : champ « description » manquant.`);
  else {
    if (description.length > 1024)
      erreurs.push(
        `${ou} : description trop longue (${description.length} caractères, 1024 au plus).`,
      );
    if (/[<>]/.test(description))
      erreurs.push(`${ou} : la description ne doit pas contenir < ou >.`);
  }
  const autorises = [
    'name',
    'description',
    'license',
    'compatibility',
    'metadata',
    'allowed-tools',
  ];
  for (const cle of Object.keys(donnees))
    if (!autorises.includes(cle))
      erreurs.push(`${ou} : clé d'en-tête non standard « ${cle} » (à ranger dans metadata).`);
  if (!VERSION_VALIDE.test(version))
    erreurs.push(`${ou} : metadata.version doit être une version x.y.z entre guillemets.`);
  if (donnees.metadata?.categorie !== skill.categorie)
    erreurs.push(`${ou} : metadata.categorie doit valoir « ${skill.categorie} » (dossier parent).`);
  const statut = donnees.metadata?.statut;
  if (statut !== undefined && !STATUTS.includes(statut))
    erreurs.push(`${ou} : metadata.statut doit valoir ${STATUTS.join(', ')}.`);
  if (donnees.metadata?.remplace_par && !['deprecie', 'retire'].includes(statut))
    erreurs.push(`${ou} : metadata.remplace_par suppose le statut deprecie ou retire.`);
  const lignes = skill.texte.split('\n').length;
  if (lignes > 500)
    erreurs.push(
      `${ou} : SKILL.md fait ${lignes} lignes (500 au plus, déplacez le détail dans references/).`,
    );
  // Fichiers cités dans SKILL.md : ils doivent exister.
  for (const [, cite] of skill.corps.matchAll(
    /(?:\]\(|`)((?:references|scripts|assets|exemples)\/[\w./-]+?)(?:\)|`)/g,
  )) {
    const present = cite.endsWith('/')
      ? skill.fichiers.some((f) => f.startsWith(cite))
      : skill.fichiers.includes(cite);
    if (!present) erreurs.push(`${ou} : fichier cité introuvable « ${cite} ».`);
  }
  return erreurs;
}

// Modèles de design-skazy, seule référence du design des skills plan et support. Ils ne sont pas copiés dans
// ce dépôt : npm run modeles les lit dans design-skazy, compare les rendus des skills avec eux et verrouille
// leur empreinte dans commun/charte/alignement.json ; npm run check refuse ensuite un modèle changé depuis.
export const MODELES = {
  'plan-formation': {
    source: 'templates/plan-formation/PlanFormation.dc.html',
    skill: 'skazy-plan-formation',
  },
  'support-formation': {
    source: 'templates/support-formation/SupportFormation.dc.html',
    skill: 'skazy-support-formation',
  },
};
export const ALIGNEMENT = join(RACINE, 'commun/charte/alignement.json');

/** Empreinte SHA-256 de chaque modèle, lu dans le dépôt design-skazy. */
export async function empreintesModeles(design) {
  const { createHash } = await import('node:crypto');
  const empreintes = {};
  for (const [nom, m] of Object.entries(MODELES))
    empreintes[nom] = createHash('sha256')
      .update(await readFile(join(design, m.source)))
      .digest('hex');
  return empreintes;
}

/** Dépôt design-skazy : $DESIGN_SKAZY, sinon un dossier design-skazy à côté de ce dépôt ou d'un parent. */
export function trouverDesign() {
  const candidats = [process.env.DESIGN_SKAZY];
  for (let d = RACINE; dirname(d) !== d; d = dirname(d))
    candidats.push(join(dirname(d), 'design-skazy'));
  return candidats.find((d) => d && existsSync(join(d, 'charte/charte.json')));
}
