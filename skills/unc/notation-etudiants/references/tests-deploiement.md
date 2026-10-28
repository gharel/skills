# Tester les déploiements

## Préparer

- **Accès réseau.** Les bacs à sable bloquent souvent les hébergeurs (`403 blocked-by-allowlist` sur onrender.com). La lecture de page par simple requête renvoie souvent une page vide sur ces sites. Passe par un navigateur piloté quand c'est possible.
- **Réveil.** Render, en offre gratuite, met les sites en veille. Ouvre d'abord tous les sites dans des onglets séparés pour les réveiller (30 à 60 s), puis teste.
- **Identité.** Vérifie que le site déployé est bien celui de l'étudiant, par le pied de page ou le titre. Le nom d'un autre étudiant signifie que ce n'est pas son déploiement. C'est une pénalité lourde : signale-la à l'enseignant, ne l'applique pas seul.

## Tester l'API depuis la page

Teste depuis la page elle-même (même origine), avec un script lancé dans la console du navigateur.

Les secrets et les jetons ne doivent **jamais** apparaître dans la sortie. N'affiche que :

- les codes HTTP ;
- les types de contenu ;
- les noms des clés JSON.

Script type pour un réducteur d'URL, à adapter aux routes de l'énoncé :

```js
const base = location.origin;
const out = [];
const j = async (p, o = {}) => {
  try {
    const r = await fetch(base + p, {
      ...o,
      headers: { Accept: 'application/json', ...(o.headers || {}) },
    });
    const t = await r.text();
    let k = '';
    try {
      k = Object.keys(JSON.parse(t)).join(',');
    } catch (e) {
      k = 'nonjson:' + t.length;
    }
    return { s: r.status, ct: (r.headers.get('content-type') || '').split(';')[0], k, t };
  } catch (e) {
    return { s: 'ERR', k: e.message, t: '' };
  }
};
const log = (n, r) => out.push(n + ' ' + r.s + ' ' + (r.ct || '') + ' [' + r.k + ']');
const json = { 'Content-Type': 'application/json' };
const u = 'https://example.org/t' + Date.now();
const p1 = await j('/api-v2/', { method: 'POST', headers: json, body: JSON.stringify({ url: u }) });
log('POST1', p1);
const p2 = await j('/api-v2/', { method: 'POST', headers: json, body: JSON.stringify({ url: u }) });
log('POST2 même url', p2);
log(
  'POST invalide',
  await j('/api-v2/', {
    method: 'POST',
    headers: json,
    body: JSON.stringify({ url: 'pas une url' }),
  }),
);
const gc = (t) => {
  try {
    const d = JSON.parse(t);
    const v = d.short || d.short_url || d.shortUrl || d.link || d.code || d.url;
    return String(v).split('/').filter(Boolean).pop();
  } catch (e) {
    return null;
  }
};
const c = gc(p1.t);
out.push('codes identiques=' + (c === gc(p2.t)));
if (c) {
  const r = await j('/api-v2/' + c);
  log('GET json', r);
  try {
    out.push('secret exposé=' + ('secret' in JSON.parse(r.t)));
  } catch (e) {}
  const x = await fetch(base + '/api-v2/' + c, {
    headers: { Accept: 'text/html' },
    redirect: 'manual',
  });
  out.push('REDIR ' + x.type);
  log('DEL sans clé', await j('/api-v2/' + c, { method: 'DELETE' }));
  log(
    'DEL mauvaise clé',
    await j('/api-v2/' + c, { method: 'DELETE', headers: { 'X-API-Key': 'zzzz' } }),
  );
  let s = null;
  try {
    s = JSON.parse(p1.t).secret;
  } catch (e) {}
  if (s)
    log(
      'DEL bonne clé',
      await j('/api-v2/' + c, { method: 'DELETE', headers: { 'X-API-Key': s } }),
    );
  else out.push('secret non renvoyé au créateur');
  log('GET inexistant', await j('/api-v2/zz9zz9'));
}
log('406', await j('/api-v2/', { headers: { Accept: 'image/png' } }));
out.join('\n');
```

## Tester l'interface comme un utilisateur

- **Client AJAX** : remplis le champ, déclenche `form.requestSubmit()`, attends 4 s, puis lis le texte de la page. Vérifie que le bouton attendu est présent (par exemple « Copier »). Un client qui appelle `http://localhost:8080/` échoue en ligne avec « Failed to fetch ».
- **Formulaire rendu côté serveur** (EJS) : soumets-le avec `form.submit()`, puis lis la page obtenue.
- **Ergonomie** : fais une capture réduite de chaque page pour en juger.
- **Nettoyage** : ferme tous les onglets ouverts à la fin.

## Sans navigateur

- **Avec un terminal** : teste les mêmes routes au `curl`, comme pour un test en local (voir [collecte-et-code.md](collecte-et-code.md)). Si l'hébergeur est bloqué, teste en local et écris « testé en local seulement ».
- **Sans aucun des deux** : écris « non testé » dans la justification. Donne à l'enseignant la liste des vérifications à faire, et le script ci-dessus à coller dans la console de son navigateur.

Note la date du test dans chaque justification (« testé en ligne le 22/10/2026 »).
