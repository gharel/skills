/**
 * npm run dev : sert le site construit (_site/, après npm run construire) sur http://localhost:4182 (PORT pour en changer).
 * Refuse un port occupé plutôt que d'en prendre un autre au hasard.
 */
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const RACINE = fileURLToPath(new URL('../_site/', import.meta.url));
const PORT = Number(process.env.PORT) || 4182;

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.woff2': 'font/woff2',
  '.json': 'application/json; charset=utf-8',
  '.md': 'text/markdown; charset=utf-8',
  '.py': 'text/x-python; charset=utf-8',
  '.zip': 'application/zip',
  '.ps1': 'text/plain; charset=utf-8',
  '.sh': 'text/plain; charset=utf-8',
  '.tsv': 'text/tab-separated-values; charset=utf-8',
  '.yaml': 'text/yaml; charset=utf-8',
};

const serveur = createServer(async (requete, reponse) => {
  let chemin = decodeURIComponent(new URL(requete.url, 'http://localhost').pathname);
  if (chemin.endsWith('/')) chemin += 'index.html';
  const fichier = normalize(join(RACINE, chemin));
  if (!fichier.startsWith(normalize(RACINE))) {
    reponse.writeHead(403).end();
    return;
  }
  try {
    const contenu = await readFile(fichier);
    reponse.writeHead(200, {
      'Content-Type': TYPES[extname(fichier)] ?? 'application/octet-stream',
    });
    reponse.end(contenu);
  } catch {
    reponse.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }).end('Introuvable');
  }
});

serveur.on('error', (erreur) => {
  if (erreur.code === 'EADDRINUSE') {
    console.error(
      `Le port ${PORT} est déjà pris : arrêtez l'autre serveur ou lancez PORT=4183 npm run dev.`,
    );
    process.exit(1);
  }
  throw erreur;
});

serveur.listen(PORT, () => console.log(`Skills IA : http://localhost:${PORT}/`));
