#!/bin/sh
# Installe ou met à jour les skills IA de gharel/skills (macOS, Linux).
#
#   curl -fsSL https://gharel.github.io/skills/installer.sh | sh
#
# Options (variables d'environnement) :
#   SKILLS="skazy-quiz,skazy-plan-formation"   seulement ces skills
#   SKILLS_CATEGORIE=pro                        seulement une catégorie (pro, unc, perso)
#   SKILLS_DOSSIER=/chemin/skills               un seul dossier cible (sinon : assistants détectés)
# Exemple : curl -fsSL https://gharel.github.io/skills/installer.sh | SKILLS_CATEGORIE=pro sh
#
# Le script télécharge la dernière version du dépôt, puis copie chaque skill dans le dossier de
# chaque assistant présent. Relancez-le pour mettre à jour : l'ancienne version est remplacée.
set -eu

ARCHIVE="https://github.com/gharel/skills/archive/refs/heads/main.tar.gz"
TEMP=$(mktemp -d)
trap 'rm -rf "$TEMP"' EXIT

echo "Téléchargement de gharel/skills…"
curl -fsSL "$ARCHIVE" | tar -xz -C "$TEMP"
RACINE=$(find "$TEMP" -mindepth 1 -maxdepth 1 -type d | head -n 1)

# Skills retenus : dossiers skills/<catégorie>/<nom>/ qui contiennent un SKILL.md.
LISTE=""
for fichier in "$RACINE"/skills/*/*/SKILL.md; do
  [ -f "$fichier" ] || continue
  dossier=$(dirname "$fichier")
  nom=$(basename "$dossier")
  categorie=$(basename "$(dirname "$dossier")")
  case "$nom" in _*) continue ;; esac
  if [ -n "${SKILLS_CATEGORIE:-}" ] && [ "$categorie" != "$SKILLS_CATEGORIE" ]; then continue; fi
  if [ -n "${SKILLS:-}" ]; then
    case ",$SKILLS," in *",$nom,"*) ;; *) continue ;; esac
  fi
  LISTE="$LISTE $dossier"
done
[ -n "$LISTE" ] || { echo "Aucun skill ne correspond à la sélection." >&2; exit 1; }

# Dossiers cibles : signe de présence de l'assistant | dossier des skills.
if [ -n "${SKILLS_DOSSIER:-}" ]; then
  CIBLES="|$SKILLS_DOSSIER"
else
  CIBLES="$HOME/.claude|$HOME/.claude/skills
|$HOME/.agents/skills
$HOME/.gemini|$HOME/.gemini/skills
$HOME/.cursor|$HOME/.cursor/skills
$HOME/.copilot|$HOME/.copilot/skills
$HOME/.config/opencode|$HOME/.config/opencode/skills
$HOME/.codeium/windsurf|$HOME/.codeium/windsurf/skills"
fi

echo "$CIBLES" | while IFS='|' read -r signe cible; do
  [ -z "$cible" ] && continue
  if [ -n "$signe" ] && [ ! -d "$signe" ]; then continue; fi
  mkdir -p "$cible"
  for dossier in $LISTE; do
    nom=$(basename "$dossier")
    rm -rf "${cible:?}/$nom"
    cp -R "$dossier" "$cible/$nom"
  done
  echo "  $cible"
done

NOMS=""
for dossier in $LISTE; do NOMS="$NOMS $(basename "$dossier")"; done
echo "Skills installés :$NOMS"
echo "Relancez cette commande pour mettre à jour. Catalogue : https://gharel.github.io/skills/"
