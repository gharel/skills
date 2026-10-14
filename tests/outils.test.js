import { describe, expect, it } from 'vitest';
import { controler, lireFrontmatter, listerSkills } from '../outils/skills.mjs';

describe('lireFrontmatter', () => {
  it('lit les clés simples, les guillemets et le bloc metadata', () => {
    const { donnees, corps } = lireFrontmatter(
      '---\nname: mon-skill\ndescription: Fait ceci. À utiliser quand…\nmetadata:\n  version: "1.2.0"\n  categorie: pro\n---\n# Titre\n',
    );
    expect(donnees).toEqual({
      name: 'mon-skill',
      description: 'Fait ceci. À utiliser quand…',
      metadata: { version: '1.2.0', categorie: 'pro' },
    });
    expect(corps).toBe('# Titre\n');
  });

  it('renvoie null sans en-tête', () => {
    expect(lireFrontmatter('# Pas d’en-tête').donnees).toBeNull();
  });
});

describe('skills du dépôt', async () => {
  const skills = await listerSkills();

  it('contient les trois skills Pro, dans l’ordre de la chaîne', () => {
    expect(skills.filter((s) => s.categorie === 'pro').map((s) => s.nom)).toEqual([
      'skazy-plan-formation',
      'skazy-support-formation',
      'skazy-quiz',
    ]);
  });

  it.each(skills.map((s) => [s.nom, s]))(
    '%s respecte la spécification Agent Skills',
    (_, skill) => {
      expect(controler(skill)).toEqual([]);
    },
  );

  it('chaque skill a un titre et un résumé pour ChatGPT (agents/openai.yaml)', () => {
    for (const s of skills) {
      expect(s.titre, s.nom).not.toBe(s.nom);
      expect(s.resume.length, s.nom).toBeGreaterThan(20);
    }
  });
});

describe('controler', () => {
  const base = {
    chemin: 'skills/pro/essai',
    categorie: 'pro',
    dossierNom: 'essai',
    texte: '---\n---\n',
    corps: 'Voir [la référence](references/absente.md).',
    fichiers: ['SKILL.md'],
  };

  it('signale un nom différent du dossier, une version et une catégorie manquantes, un fichier cité absent', () => {
    const erreurs = controler({
      ...base,
      nom: 'Autre_Nom',
      description: 'Décrit <le> skill',
      version: '',
      donnees: { name: 'Autre_Nom', description: 'x', metadata: {} },
    });
    expect(erreurs.join('\n')).toMatch(/nom du dossier/);
    expect(erreurs.join('\n')).toMatch(/minuscules/);
    expect(erreurs.join('\n')).toMatch(/< ou >/);
    expect(erreurs.join('\n')).toMatch(/metadata.version/);
    expect(erreurs.join('\n')).toMatch(/metadata.categorie/);
    expect(erreurs.join('\n')).toMatch(/references\/absente.md/);
  });

  it('refuse un en-tête YAML invalide (deux-points sans guillemets)', () => {
    const description = 'Trois sorties au choix : Kahoot ou Forms';
    const erreurs = controler({
      ...base,
      texte: `---\nname: essai\ndescription: ${description}\n---\n`,
      corps: '',
      nom: 'essai',
      description,
      version: '1.0.0',
      donnees: { name: 'essai', description, metadata: { version: '1.0.0', categorie: 'pro' } },
    });
    expect(erreurs.join('\n')).toMatch(/YAML invalide/);
  });

  it('refuse une clé d’en-tête hors spécification', () => {
    const erreurs = controler({
      ...base,
      corps: '',
      nom: 'essai',
      description: 'Un skill.',
      version: '1.0.0',
      donnees: {
        name: 'essai',
        description: 'Un skill.',
        version: '1.0.0',
        metadata: { version: '1.0.0', categorie: 'pro' },
      },
    });
    expect(erreurs).toEqual([
      "skills/pro/essai : clé d'en-tête non standard « version » (à ranger dans metadata).",
    ]);
  });
});
