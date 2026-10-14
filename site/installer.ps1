# Installe ou met à jour les skills IA de gharel/skills (Windows, PowerShell 5.1 ou 7).
#
#   irm https://gharel.github.io/skills/installer.ps1 | iex
#
# Options (variables d'environnement, avant la commande) :
#   $env:SKILLS = "skazy-quiz,skazy-plan-formation"   seulement ces skills
#   $env:SKILLS_CATEGORIE = "pro"                     seulement une catégorie (pro, unc, perso)
#   $env:SKILLS_DOSSIER = "C:\chemin\skills"          un seul dossier cible (sinon : assistants détectés)
#
# Le script télécharge la dernière version du dépôt, puis copie chaque skill dans le dossier de
# chaque assistant présent. Relancez-le pour mettre à jour : l'ancienne version est remplacée.

$ErrorActionPreference = 'Stop'
# Messages en ASCII : Windows PowerShell 5.1 lit ce script en Latin-1 via irm, les accents passent
# donc par leur code (é = 0xE9, à = 0xE0, … = 0x2026).
$e = [char]0xE9; $a = [char]0xE0; $pp = [char]0x2026
$ProgressPreference = 'SilentlyContinue'

$archive = 'https://github.com/gharel/skills/archive/refs/heads/main.zip'
$accueil = [Environment]::GetFolderPath('UserProfile')
$temp = Join-Path ([IO.Path]::GetTempPath()) ('skills-' + [guid]::NewGuid().ToString('N'))

# Dossiers des assistants : (dossier de configuration qui signale l'assistant, dossier des skills).
$assistants = @(
  @{ Nom = 'Claude Code'; Signe = '.claude'; Cible = '.claude\skills' },
  @{ Nom = 'Codex et agents compatibles'; Signe = ''; Cible = '.agents\skills' },
  @{ Nom = 'Gemini CLI'; Signe = '.gemini'; Cible = '.gemini\skills' },
  @{ Nom = 'Cursor'; Signe = '.cursor'; Cible = '.cursor\skills' },
  @{ Nom = 'GitHub Copilot'; Signe = '.copilot'; Cible = '.copilot\skills' },
  @{ Nom = 'OpenCode'; Signe = '.config\opencode'; Cible = '.config\opencode\skills' },
  @{ Nom = 'Windsurf'; Signe = '.codeium\windsurf'; Cible = '.codeium\windsurf\skills' }
)

try {
  Write-Host "T${e}l${e}chargement de gharel/skills$pp"
  New-Item -ItemType Directory -Path $temp | Out-Null
  Invoke-WebRequest -Uri $archive -OutFile "$temp\depot.zip" -UseBasicParsing
  Expand-Archive -Path "$temp\depot.zip" -DestinationPath $temp -Force
  $racine = Get-ChildItem -Path $temp -Directory | Select-Object -First 1

  $choix = @()
  if ($env:SKILLS) { $choix = $env:SKILLS.Split(',') | ForEach-Object { $_.Trim() } }
  $skills = Get-ChildItem -Path (Join-Path $racine.FullName 'skills') -Recurse -Filter 'SKILL.md' |
    ForEach-Object { $_.Directory } |
    Where-Object { -not $_.Name.StartsWith('_') } |
    Where-Object { -not $env:SKILLS_CATEGORIE -or $_.Parent.Name -eq $env:SKILLS_CATEGORIE } |
    Where-Object { $choix.Count -eq 0 -or $choix -contains $_.Name }
  if (-not $skills) { throw "Aucun skill ne correspond $a la s${e}lection." }

  if ($env:SKILLS_DOSSIER) {
    $cibles = @(@{ Nom = 'Dossier choisi'; Chemin = $env:SKILLS_DOSSIER })
  } else {
    $cibles = foreach ($assistant in $assistants) {
      if (-not $assistant.Signe -or (Test-Path (Join-Path $accueil $assistant.Signe))) {
        @{ Nom = $assistant.Nom; Chemin = (Join-Path $accueil $assistant.Cible) }
      }
    }
  }

  foreach ($cible in $cibles) {
    New-Item -ItemType Directory -Force -Path $cible.Chemin | Out-Null
    foreach ($skill in $skills) {
      $destination = Join-Path $cible.Chemin $skill.Name
      if (Test-Path $destination) { Remove-Item -Recurse -Force -Path $destination }
      Copy-Item -Recurse -Path $skill.FullName -Destination $destination
    }
    Write-Host ("  {0} : {1}" -f $cible.Nom, $cible.Chemin)
  }
  Write-Host ("{0} skill(s) install${e}(s) : {1}" -f $skills.Count, (($skills | ForEach-Object Name) -join ', '))
  Write-Host "Relancez cette commande pour mettre $a jour. Catalogue : https://gharel.github.io/skills/"
} finally {
  if (Test-Path $temp) { Remove-Item -Recurse -Force -Path $temp }
}
