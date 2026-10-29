#!/bin/sh
# Installe, met à jour ou désinstalle les skills IA de gharel/skills (macOS, Linux, WSL).
#
#   curl -fsSL https://gharel.github.io/skills/installer.sh | sh
#
# Une seule copie de chaque skill, dans ~/.agents/skills : Codex, Gemini CLI, GitHub Copilot, Cursor et
# OpenCode lisent ce dossier. Claude Code et Windsurf reçoivent un lien par skill vers cette copie
# (Claude Code n'en reçoit pas si le plugin gharel-skills est installé). Le manifeste
# ~/.agents/.gharel-skills/manifeste.tsv retient ce que le script a installé : il ne remplace ou ne
# supprime que ces dossiers, et sauvegarde un skill personnel du même nom. Les fichiers viennent du site
# publié, après les contrôles de la CI. Relancez la commande pour mettre à jour.
#
# Sous WSL, le script installe pour les assistants lancés dans la distribution, puis pour ceux de
# Windows (installer.ps1 par powershell.exe). Sous Git Bash, MSYS ou Cygwin, il passe la main à installer.ps1.
#
# Options (variables d'environnement) :
#   SKILLS="skazy-quiz,skazy-plan-formation"   seulement ces skills ("tout" : retour à tous)
#   SKILLS_CATEGORIE=pro                        seulement ces catégories : pro, unc, perso ("tout")
#   SKILLS_AUTO=1                               mise à jour quotidienne (launchd, systemd ou cron) ; 0 la retire
#   SKILLS_ACTION=desinstaller                  retire tout ce que le script a installé
#   SKILLS_DOSSIER=/chemin/skills               un seul dossier cible, sans lien
#   SKILLS_WINDOWS=0                            sous WSL, ne pas installer aussi côté Windows
# Exemple : curl -fsSL https://gharel.github.io/skills/installer.sh | SKILLS_CATEGORIE=pro sh
# La sélection (SKILLS, SKILLS_CATEGORIE) et le choix SKILLS_AUTO sont retenus pour les fois suivantes.
# Pour les tests : SKILLS_SITE (adresse du site), SKILLS_ACCUEIL (dossier personnel), SKILLS_AUTO=essai.
set -eu

SITE="${SKILLS_SITE:-https://gharel.github.io/skills/}"
case "$SITE" in */) ;; *) SITE="$SITE/" ;; esac
ACCUEIL="${SKILLS_ACCUEIL:-$HOME}"
MARQUE='source: https://github.com/gharel/skills'
LABEL='nc.skazy.gharel-skills'
TAB=$(printf '\t')
NL='
'

dire() { [ "${SKILLS_SILENCIEUX:-}" = 1 ] || printf '%s\n' "$*"; }
erreur() {
  printf '%s\n' "$*" >&2
  exit 1
}

# Windows hors WSL : installer.ps1 fait le travail (ln -s n'y crée que des copies).
case "$(uname -s)" in
MINGW* | MSYS* | CYGWIN*)
  dire "Windows : installation par PowerShell…"
  exec powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "irm '${SITE}installer.ps1' | iex"
  ;;
esac
WSL=''
if [ -n "${WSL_DISTRO_NAME:-}" ] || grep -qiE 'microsoft-standard|microsoft@microsoft' /proc/version 2>/dev/null; then
  WSL=1
fi

# Assistants : nom | dossier qui le signale | dossier des skills où poser un lien (vide : il lit
# ~/.agents/skills).
ASSISTANTS='Claude Code|.claude|.claude/skills
Codex|.codex|
Gemini CLI|.gemini|
GitHub Copilot|.copilot|
Cursor|.cursor|
OpenCode|.config/opencode|
Windsurf|.codeium/windsurf|.codeium/windsurf/skills'
# Copies laissées par les anciennes versions de l'installeur : en double avec ~/.agents/skills.
ANCIENNES_CIBLES='.gemini/skills .cursor/skills .copilot/skills .config/opencode/skills'

if [ -n "${SKILLS_DOSSIER:-}" ]; then
  CANONIQUE="$SKILLS_DOSSIER"
  ETAT="$(dirname "$SKILLS_DOSSIER")/.gharel-skills"
else
  CANONIQUE="$ACCUEIL/.agents/skills"
  ETAT="$ACCUEIL/.agents/.gharel-skills"
fi
MANIFESTE="$ETAT/manifeste.tsv"
TMP="$ETAT/tmp"

telecharger() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$1" -o "$2"
  elif command -v wget >/dev/null 2>&1; then
    wget -q "$1" -O "$2"
  else
    erreur "Il faut curl ou wget."
  fi
}
extraire() {
  if command -v unzip >/dev/null 2>&1; then
    unzip -q -o "$1" -d "$2"
  elif command -v python3 >/dev/null 2>&1; then
    python3 -m zipfile -e "$1" "$2"
  else
    erreur "Il faut unzip (sudo apt install unzip, ou dnf, pacman…) ou python3."
  fi
}
# Lignes du manifeste d'un type donné (et d'une clé, facultative).
manifeste() {
  [ -f "$MANIFESTE" ] || return 0
  awk -F "$TAB" -v t="$1" -v k="${2:-}" '$1 == t && (k == "" || $2 == k)' "$MANIFESTE"
}
existe() { [ -e "$1" ] || [ -L "$1" ]; }
# Un lien se supprime seul, jamais sa cible.
supprimer() {
  if [ -L "$1" ]; then
    rm -f "$1"
  elif [ -e "$1" ]; then
    rm -rf "$1"
  fi
}
# Un dossier est à nous s'il figure au manifeste ou si son SKILL.md cite le dépôt.
a_nous() {
  case "$NL$CONNUS$NL" in *"$NL$1$NL"*) return 0 ;; esac
  [ -f "$1/SKILL.md" ] && grep -qF "$MARQUE" "$1/SKILL.md"
}
dans() { case ",$2," in *",$1,"*) return 0 ;; esac; return 1; }
sauvegarder() {
  mkdir -p "$ETAT/sauvegardes"
  copie="$ETAT/sauvegardes/$(basename "$1")-$(date +%Y%m%d%H%M%S)"
  mv "$1" "$copie"
  SAUVEGARDES="$SAUVEGARDES$1$TAB$copie$NL"
  dire "  ! $1 n'est pas un skill gharel/skills : sauvegardé dans $copie"
}

# ── Mise à jour quotidienne : launchd (macOS), timer systemd utilisateur, sinon cron ──
inscrire_tache() {
  essai="${1:-}"
  mkdir -p "$ETAT"
  # Copie locale lancée par la tâche, remplacée d'un coup (un script en cours de lecture ne doit
  # pas être réécrit sur place).
  telecharger "${SITE}installer.sh" "$ETAT/installer.sh.nouveau"
  mv -f "$ETAT/installer.sh.nouveau" "$ETAT/installer.sh"
  case "$(uname -s)" in
  Darwin)
    plist="$ACCUEIL/Library/LaunchAgents/$LABEL.plist"
    mkdir -p "$(dirname "$plist")"
    cat >"$plist" <<FIN
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>/bin/sh</string><string>$ETAT/installer.sh</string></array>
  <key>EnvironmentVariables</key>
  <dict><key>SKILLS_SILENCIEUX</key><string>1</string></dict>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardErrorPath</key><string>$ETAT/journal.log</string>
</dict>
</plist>
FIN
    if [ "$essai" = essai ]; then
      dire "  (essai) LaunchAgent écrit : $plist"
      return 0
    fi
    launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$plist"
    dire "Mise à jour automatique : LaunchAgent $LABEL, chaque jour à 9 h (SKILLS_AUTO=0 pour le retirer)."
    ;;
  *)
    if [ "$essai" = essai ] || systemctl --user show-environment >/dev/null 2>&1; then
      unites="$ACCUEIL/.config/systemd/user"
      mkdir -p "$unites"
      cat >"$unites/gharel-skills.service" <<FIN
[Unit]
Description=Mise a jour des skills IA gharel/skills

[Service]
Type=oneshot
Environment=SKILLS_SILENCIEUX=1 SKILLS_WINDOWS=0
ExecStart=/bin/sh "$ETAT/installer.sh"
FIN
      cat >"$unites/gharel-skills.timer" <<FIN
[Unit]
Description=Mise a jour quotidienne des skills IA gharel/skills

[Timer]
OnCalendar=*-*-* 09:00:00
Persistent=true
RandomizedDelaySec=15min

[Install]
WantedBy=timers.target
FIN
      if [ "$essai" = essai ]; then
        dire "  (essai) timer systemd écrit : $unites/gharel-skills.timer"
        return 0
      fi
      systemctl --user daemon-reload
      systemctl --user enable --now gharel-skills.timer >/dev/null 2>&1
      dire "Mise à jour automatique : timer systemd gharel-skills, chaque jour (SKILLS_AUTO=0 pour le retirer)."
    elif command -v crontab >/dev/null 2>&1 &&
      { [ -z "$WSL" ] || pgrep -x cron >/dev/null 2>&1 || pgrep -x crond >/dev/null 2>&1; }; then
      {
        crontab -l 2>/dev/null | grep -v '# gharel-skills' || true
        echo "0 9 * * * SKILLS_SILENCIEUX=1 SKILLS_WINDOWS=0 /bin/sh \"$ETAT/installer.sh\" >/dev/null 2>&1 # gharel-skills"
      } | crontab -
      dire "Mise à jour automatique : crontab, chaque jour à 9 h (SKILLS_AUTO=0 pour la retirer)."
    else
      if [ -n "$WSL" ]; then
        dire "Mise à jour automatique impossible : WSL sans systemd ni cron. Ajoutez [boot] systemd=true dans /etc/wsl.conf, lancez wsl --shutdown depuis Windows, puis relancez avec SKILLS_AUTO=1."
      else
        dire "Mise à jour automatique impossible : ni systemd utilisateur ni crontab. Relancez la commande de temps en temps."
      fi
      rm -f "$ETAT/installer.sh"
      AUTO=0
    fi
    ;;
  esac
}
retirer_tache() {
  plist="$ACCUEIL/Library/LaunchAgents/$LABEL.plist"
  if [ -f "$plist" ]; then
    launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
    rm -f "$plist"
    dire "LaunchAgent $LABEL retiré."
  fi
  unites="$ACCUEIL/.config/systemd/user"
  if [ -f "$unites/gharel-skills.timer" ]; then
    systemctl --user disable --now gharel-skills.timer >/dev/null 2>&1 || true
    rm -f "$unites/gharel-skills.timer" "$unites/gharel-skills.service"
    systemctl --user daemon-reload >/dev/null 2>&1 || true
    dire "Timer systemd gharel-skills retiré."
  fi
  if command -v crontab >/dev/null 2>&1 && crontab -l 2>/dev/null | grep -q '# gharel-skills'; then
    crontab -l 2>/dev/null | grep -v '# gharel-skills' | crontab -
    dire "Ligne crontab gharel-skills retirée."
  fi
  rm -f "$ETAT/installer.sh"
}

# ── Sous WSL : même opération côté Windows, pour les assistants lancés hors de la distribution ──
windows_aussi() {
  [ -n "$WSL" ] && [ "${SKILLS_WINDOWS:-1}" != 0 ] && [ -z "${SKILLS_DOSSIER:-}" ] || return 0
  if ! command -v powershell.exe >/dev/null 2>&1; then
    dire "Windows : powershell.exe introuvable depuis WSL. Lancez dans PowerShell : irm ${SITE}installer.ps1 | iex"
    return 0
  fi
  dire ""
  dire "Windows (assistants lancés hors de WSL) :"
  SKILLS_DEPUIS_WSL=1
  WSLENV="SKILLS:SKILLS_CATEGORIE:SKILLS_AUTO:SKILLS_ACTION:SKILLS_SITE:SKILLS_SILENCIEUX:SKILLS_DEPUIS_WSL${WSLENV:+:$WSLENV}"
  export SKILLS_DEPUIS_WSL WSLENV
  (cd /mnt/c 2>/dev/null || cd /; powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "irm '${SITE}installer.ps1' | iex") ||
    dire "Windows : échec. Lancez dans PowerShell : irm ${SITE}installer.ps1 | iex"
}

# ── Désinstallation ──
CONNUS=''
SAUVEGARDES=''
if [ "${SKILLS_ACTION:-}" = desinstaller ] && [ ! -f "$MANIFESTE" ]; then
  dire "Aucune installation gharel/skills dans $CANONIQUE."
  windows_aussi
  exit 0
fi
if [ "${SKILLS_ACTION:-}" = desinstaller ]; then
  manifeste lien | cut -f3 | while IFS= read -r lien; do
    if [ -L "$lien" ] || a_nous "$lien"; then supprimer "$lien"; fi
  done
  n=0
  for nom in $(manifeste skill | cut -f2); do
    supprimer "$CANONIQUE/$nom"
    n=$((n + 1))
  done
  manifeste sauvegarde | while IFS="$TAB" read -r _ origine copie; do
    if existe "$copie" && ! existe "$origine"; then
      mv "$copie" "$origine"
      dire "  Restauré : $origine"
    fi
  done
  if [ "$(manifeste auto | cut -f2)" = 1 ]; then retirer_tache; fi
  rm -f "$MANIFESTE" "$ETAT/installer.sh"
  supprimer "$TMP"
  rmdir "$ETAT/sauvegardes" "$ETAT" "$CANONIQUE" 2>/dev/null || true
  dire "$n skill(s) désinstallé(s) de $CANONIQUE."
  windows_aussi
  exit 0
fi
[ -z "${SKILLS_ACTION:-}" ] || erreur "SKILLS_ACTION inconnue : $SKILLS_ACTION (seule valeur : desinstaller)."

# ── Sélection : variables d'environnement, sinon celle de la dernière fois ──
choix_skills=$(manifeste selection skills | cut -f3)
[ -z "${SKILLS:-}" ] || choix_skills="$SKILLS"
[ "$choix_skills" != tout ] || choix_skills=''
choix_skills=$(printf '%s' "$choix_skills" | tr -d ' ')
choix_categories=$(manifeste selection categories | cut -f3)
[ -z "${SKILLS_CATEGORIE:-}" ] || choix_categories="$SKILLS_CATEGORIE"
[ "$choix_categories" != tout ] || choix_categories=''
choix_categories=$(printf '%s' "$choix_categories" | tr -d ' ')

dire "gharel/skills : lecture du catalogue…"
mkdir -p "$CANONIQUE" "$ETAT"
supprimer "$TMP"
mkdir -p "$TMP"
trap 'supprimer "$TMP"' EXIT
telecharger "${SITE}skills.tsv" "$TMP/skills.tsv"
for nom in $(printf '%s' "$choix_skills" | tr ',' ' '); do
  awk -F "$TAB" -v n="$nom" '$1 == n { trouve = 1 } END { exit !trouve }' "$TMP/skills.tsv" ||
    dire "  ? $nom : skill inconnu du catalogue."
done

# Skills voulus : recommandés (ou nommés dans SKILLS), dépréciés s'ils sont déjà là, jamais retirés.
anciens=$(manifeste skill | cut -f2 | tr '\n' ' ')
VOULUS=''
while IFS="$TAB" read -r nom categorie version statut remplace; do
  case "$nom" in '' | '#'*) continue ;; esac
  [ "$statut" != retire ] || continue
  [ -z "$choix_categories" ] || dans "$categorie" "$choix_categories" || continue
  if [ -n "$choix_skills" ]; then
    dans "$nom" "$choix_skills" || continue
  elif [ "$statut" = deprecie ]; then
    case " $anciens " in *" $nom "*) ;; *) continue ;; esac
  elif [ "$statut" != recommande ]; then
    continue
  fi
  VOULUS="$VOULUS$nom$TAB$version$TAB$statut$TAB$remplace$NL"
done <"$TMP/skills.tsv"
[ -n "$VOULUS" ] || erreur "Aucun skill ne correspond à la sélection."
noms_voulus=$(printf '%s' "$VOULUS" | cut -f1 | tr '\n' ' ')
CONNUS=$(
  for nom in $anciens; do printf '%s\n' "$CANONIQUE/$nom"; done
  manifeste lien | cut -f3
)
SAUVEGARDES=$(manifeste sauvegarde | cut -f2-)
[ -z "$SAUVEGARDES" ] || SAUVEGARDES="$SAUVEGARDES$NL"

# ── Copies dans ~/.agents/skills : seulement les skills nouveaux ou changés ──
BILAN=''
while IFS="$TAB" read -r nom version statut remplace; do
  [ -n "$nom" ] || continue
  dest="$CANONIQUE/$nom"
  avant=$(manifeste skill "$nom" | cut -f3)
  if [ "$avant" = "$version" ] && [ -f "$dest/SKILL.md" ]; then
    BILAN="$BILAN  = $nom $version$NL"
  else
    telecharger "${SITE}telechargements/$nom.zip" "$TMP/$nom.zip"
    extraire "$TMP/$nom.zip" "$TMP/$nom"
    if existe "$dest"; then
      if a_nous "$dest"; then supprimer "$dest"; else sauvegarder "$dest"; fi
    fi
    mv "$TMP/$nom/$nom" "$dest"
    if [ -n "$avant" ]; then
      BILAN="$BILAN  ^ $nom $avant -> $version$NL"
    else
      BILAN="$BILAN  + $nom $version$NL"
    fi
  fi
  if [ "$statut" = deprecie ]; then
    if [ "$remplace" != - ]; then
      BILAN="$BILAN    $nom est déprécié, remplacé par $remplace.$NL"
    else
      BILAN="$BILAN    $nom est déprécié.$NL"
    fi
  fi
done <<FIN
$VOULUS
FIN
for nom in $anciens; do
  case " $noms_voulus " in *" $nom "*) continue ;; esac
  supprimer "$CANONIQUE/$nom"
  raison='hors sélection'
  case "$(awk -F "$TAB" -v n="$nom" '$1 == n { print $4 }' "$TMP/skills.tsv")" in
  '' | retire) raison='retiré du catalogue' ;;
  esac
  BILAN="$BILAN  - $nom ($raison)$NL"
done

# ── Liens pour les assistants qui ne lisent pas ~/.agents/skills ──
PLUGIN=''
if [ -f "$ACCUEIL/.claude/plugins/installed_plugins.json" ] &&
  grep -qF '@gharel-skills"' "$ACCUEIL/.claude/plugins/installed_plugins.json"; then
  PLUGIN=1
fi
manifeste lien | cut -f3 | while IFS= read -r lien; do
  if [ -L "$lien" ] || a_nous "$lien"; then supprimer "$lien"; fi
done
LIENS=''
LIGNES_LIENS=''
if [ -z "${SKILLS_DOSSIER:-}" ]; then
  while IFS='|' read -r nom_assistant signe relatif; do
    [ -n "$relatif" ] && [ -d "$ACCUEIL/$signe" ] || continue
    if [ "$nom_assistant" = 'Claude Code' ] && [ -n "$PLUGIN" ]; then continue; fi
    dossier="$ACCUEIL/$relatif"
    mkdir -p "$dossier"
    forme=liens
    for nom in $noms_voulus; do
      lien="$dossier/$nom"
      if existe "$lien"; then
        if [ -L "$lien" ] || a_nous "$lien"; then supprimer "$lien"; else sauvegarder "$lien"; fi
      fi
      if ! ln -s "$CANONIQUE/$nom" "$lien" 2>/dev/null; then
        cp -R "$CANONIQUE/$nom" "$lien"
        forme='copies (liens refusés)'
      fi
      LIENS="$LIENS$nom$TAB$lien$NL"
    done
    LIGNES_LIENS="$LIGNES_LIENS  $nom_assistant : $forme dans $dossier$NL"
  done <<FIN
$ASSISTANTS
FIN
fi

# ── Copies en double laissées par les anciennes versions de l'installeur ──
NETTOYES=0
if [ -z "${SKILLS_DOSSIER:-}" ]; then
  dossiers="$ANCIENNES_CIBLES"
  [ -z "$PLUGIN" ] || dossiers="$dossiers .claude/skills"
  for relatif in $dossiers; do
    for nom in $(grep -v '^#' "$TMP/skills.tsv" | cut -f1); do
      p="$ACCUEIL/$relatif/$nom"
      if [ -d "$p" ] && [ ! -L "$p" ] && [ -f "$p/SKILL.md" ] && grep -qF "$MARQUE" "$p/SKILL.md"; then
        supprimer "$p"
        NETTOYES=$((NETTOYES + 1))
      fi
    done
  done
fi

# ── Mise à jour automatique ──
AUTO=$(manifeste auto | cut -f2)
AUTO=${AUTO:-0}
if [ -n "${SKILLS_AUTO:-}" ] && [ -n "${SKILLS_DOSSIER:-}" ]; then
  dire "SKILLS_AUTO ignoré avec SKILLS_DOSSIER."
else
  case "${SKILLS_AUTO:-}" in
  1)
    AUTO=1
    inscrire_tache
    ;;
  0)
    AUTO=0
    retirer_tache
    ;;
  essai) inscrire_tache essai ;;
  '')
    if [ "$AUTO" = 1 ]; then
      telecharger "${SITE}installer.sh" "$ETAT/installer.sh.nouveau"
      mv -f "$ETAT/installer.sh.nouveau" "$ETAT/installer.sh"
    fi
    ;;
  *) erreur "SKILLS_AUTO : 1, 0 ou essai." ;;
  esac
fi

# ── Nouveau manifeste ──
{
  echo '# gharel/skills : manifeste tenu par installer.sh (ne pas modifier)'
  printf 'selection\tskills\t%s\n' "$choix_skills"
  printf 'selection\tcategories\t%s\n' "$choix_categories"
  printf 'auto\t%s\n' "$AUTO"
  printf '%s' "$VOULUS" | while IFS="$TAB" read -r nom version _; do
    if [ -n "$nom" ]; then printf 'skill\t%s\t%s\n' "$nom" "$version"; fi
  done
  printf '%s' "$LIENS" | while IFS="$TAB" read -r nom lien; do
    if [ -n "$nom" ]; then printf 'lien\t%s\t%s\n' "$nom" "$lien"; fi
  done
  printf '%s' "$SAUVEGARDES" | while IFS="$TAB" read -r origine copie; do
    if [ -n "$origine" ] && existe "$copie"; then printf 'sauvegarde\t%s\t%s\n' "$origine" "$copie"; fi
  done
} >"$MANIFESTE.nouveau"
mv -f "$MANIFESTE.nouveau" "$MANIFESTE"

# ── Bilan ──
dire "$(printf '%s' "$VOULUS" | grep -c .) skill(s) dans $CANONIQUE"
[ -z "$BILAN" ] || dire "$(printf '%s' "$BILAN")"
if [ -z "${SKILLS_DOSSIER:-}" ]; then
  lecteurs=''
  while IFS='|' read -r nom_assistant signe relatif; do
    if [ -z "$relatif" ] && [ -d "$ACCUEIL/$signe" ]; then lecteurs="$lecteurs${lecteurs:+, }$nom_assistant"; fi
  done <<FIN
$ASSISTANTS
FIN
  if [ -n "$lecteurs" ]; then
    dire "  Lu par : $lecteurs."
  else
    dire "  Lu par Codex, Gemini CLI, GitHub Copilot, Cursor et OpenCode."
  fi
fi
[ -z "$LIGNES_LIENS" ] || dire "$(printf '%s' "$LIGNES_LIENS")"
[ -z "$PLUGIN" ] || dire "  Claude Code : plugin gharel-skills installé, mis à jour par /plugin marketplace update gharel-skills."
[ "$NETTOYES" = 0 ] || dire "  $NETTOYES ancienne(s) copie(s) en double retirée(s)."
[ "$AUTO" = 1 ] || dire "Relancez cette commande pour mettre à jour, ou ajoutez SKILLS_AUTO=1 pour le faire chaque jour."
dire "Catalogue : $SITE"
windows_aussi
