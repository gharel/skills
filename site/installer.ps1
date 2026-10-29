# Installe, met à jour ou désinstalle les skills IA de gharel/skills (Windows, PowerShell 5.1 ou 7).
#
#   irm https://gharel.github.io/skills/installer.ps1 | iex
#
# Une seule copie de chaque skill, dans ~/.agents/skills : Codex, Gemini CLI, GitHub Copilot, Cursor et
# OpenCode lisent ce dossier. Claude Code et Windsurf reçoivent une jonction par skill vers cette copie
# (Claude Code n'en reçoit pas si le plugin gharel-skills est installé). Le manifeste
# ~/.agents/.gharel-skills/manifeste.tsv retient ce que le script a installé : il ne remplace ou ne
# supprime que ces dossiers, et sauvegarde un skill personnel du même nom. Les fichiers viennent du site
# publié, après les contrôles de la CI. Relancez la commande pour mettre à jour.
#
# Options (variables d'environnement, avant la commande) :
#   $env:SKILLS = "skazy-quiz,skazy-plan-formation"   seulement ces skills ("tout" : retour à tous)
#   $env:SKILLS_CATEGORIE = "pro"                     seulement ces catégories : pro, unc, perso ("tout")
#   $env:SKILLS_AUTO = "1"                            mise à jour quotidienne (tâche planifiée) ; "0" la retire
#   $env:SKILLS_ACTION = "desinstaller"               retire tout ce que le script a installé
#   $env:SKILLS_DOSSIER = "C:\chemin\skills"          un seul dossier cible, sans jonction
# La sélection (SKILLS, SKILLS_CATEGORIE) et le choix SKILLS_AUTO sont retenus pour les fois suivantes.
# Pour les tests : SKILLS_SITE (adresse du site), SKILLS_ACCUEIL (dossier personnel), SKILLS_AUTO=essai.

& {
  param([bool] $silencieux)
  $ErrorActionPreference = 'Stop'
  $ProgressPreference = 'SilentlyContinue'
  # Messages en ASCII : Windows PowerShell 5.1 lit ce script en Latin-1 via irm, les accents passent
  # donc par leur code (é = 0xE9, à = 0xE0, â = 0xE2, … = 0x2026).
  $e = [char]0xE9; $a = [char]0xE0; $ac = [char]0xE2; $pp = [char]0x2026

  $windows = ($PSVersionTable.PSEdition -eq 'Desktop') -or $IsWindows
  $site = 'https://gharel.github.io/skills/'
  if ($env:SKILLS_SITE) { $site = $env:SKILLS_SITE.TrimEnd('/') + '/' }
  $accueil = [Environment]::GetFolderPath('UserProfile')
  if ($env:SKILLS_ACCUEIL) { $accueil = $env:SKILLS_ACCUEIL }
  $marque = 'source: https://github.com/gharel/skills'

  function Chemin { [IO.Path]::Combine([string[]] ($args | ForEach-Object { $_ })) }
  function Liste($texte) { @("$texte" -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
  function Dire($texte) { if (-not $silencieux) { Write-Host $texte } }
  function Existe($chemin) { [bool](Get-Item -LiteralPath $chemin -Force -ErrorAction SilentlyContinue) }
  function EstLien($chemin) {
    $item = Get-Item -LiteralPath $chemin -Force -ErrorAction SilentlyContinue
    [bool]($item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint))
  }
  # Un dossier est à nous s'il figure au manifeste ou si son SKILL.md cite le dépôt.
  function ANous($chemin, $connus) {
    if ($connus -contains $chemin) { return $true }
    $skill = Join-Path $chemin 'SKILL.md'
    (Test-Path -LiteralPath $skill) -and [bool](Select-String -LiteralPath $skill -SimpleMatch $marque -Quiet)
  }
  function Supprimer($chemin) {
    $item = Get-Item -LiteralPath $chemin -Force -ErrorAction SilentlyContinue
    if (-not $item) { return }
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
      # Jonction ou lien : on retire le lien seul (Remove-Item -Recurse viderait la cible en 5.1).
      if ($windows) { [IO.Directory]::Delete($chemin) } else { Remove-Item -LiteralPath $chemin -Force }
    } else {
      Remove-Item -LiteralPath $chemin -Recurse -Force
    }
  }

  # Assistants : dossier qui signale l'assistant, et dossier des skills où poser une jonction.
  # Sans jonction, l'assistant lit ~/.agents/skills.
  $assistants = @(
    @{ Nom = 'Claude Code'; Signe = '.claude'; Lien = '.claude/skills' },
    @{ Nom = 'Codex'; Signe = '.codex'; Lien = '' },
    @{ Nom = 'Gemini CLI'; Signe = '.gemini'; Lien = '' },
    @{ Nom = 'GitHub Copilot'; Signe = '.copilot'; Lien = '' },
    @{ Nom = 'Cursor'; Signe = '.cursor'; Lien = '' },
    @{ Nom = 'OpenCode'; Signe = '.config/opencode'; Lien = '' },
    @{ Nom = 'Windsurf'; Signe = '.codeium/windsurf'; Lien = '.codeium/windsurf/skills' }
  )
  # Copies laissées par les anciennes versions de l'installeur : en double avec ~/.agents/skills.
  $anciennesCibles = @('.gemini/skills', '.cursor/skills', '.copilot/skills', '.config/opencode/skills')

  if ($env:SKILLS_DOSSIER) {
    $canonique = $env:SKILLS_DOSSIER
    $etat = Chemin (Split-Path $canonique -Parent) '.gharel-skills'
  } else {
    $canonique = Chemin $accueil '.agents' 'skills'
    $etat = Chemin $accueil '.agents' '.gharel-skills'
  }
  $manifeste = Chemin $etat 'manifeste.tsv'
  $tmp = Chemin $etat 'tmp'

  # ── Manifeste de l'installation précédente ──
  $ancien = @{ skills = @{}; liens = @(); sauvegardes = @(); skillsChoisis = ''; categories = ''; auto = '0' }
  if (Test-Path -LiteralPath $manifeste) {
    foreach ($ligne in Get-Content -LiteralPath $manifeste -Encoding UTF8) {
      $c = $ligne -split "`t"
      if ($c[0] -eq 'skill') { $ancien.skills[$c[1]] = $c[2] }
      elseif ($c[0] -eq 'lien') { $ancien.liens += , @{ Nom = $c[1]; Chemin = $c[2] } }
      elseif ($c[0] -eq 'sauvegarde') { $ancien.sauvegardes += , @{ Origine = $c[1]; Copie = $c[2] } }
      elseif ($c[0] -eq 'selection' -and $c[1] -eq 'skills') { $ancien.skillsChoisis = $c[2] }
      elseif ($c[0] -eq 'selection' -and $c[1] -eq 'categories') { $ancien.categories = $c[2] }
      elseif ($c[0] -eq 'auto') { $ancien.auto = $c[1] }
    }
  }

  # ── Mise à jour quotidienne : tâche planifiée de l'utilisateur, sans droits administrateur ──
  function InscrireTache([bool] $essai) {
    if (-not $windows) { Dire 'SKILLS_AUTO : sous macOS ou Linux, utilisez installer.sh.'; return }
    $local = Chemin $etat 'installer.ps1'
    Invoke-WebRequest -Uri ($site + 'installer.ps1') -OutFile $local -UseBasicParsing
    $arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $local + '" -silencieux'
    if ($essai) { Dire "  (essai) t${ac}che gharel-skills : powershell.exe $arguments"; return }
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arguments
    $declencheur = New-ScheduledTaskTrigger -Daily -At '09:00'
    $reglages = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
      -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
    Register-ScheduledTask -TaskName 'gharel-skills' -Action $action -Trigger $declencheur `
      -Settings $reglages -Description 'Mise a jour quotidienne des skills IA gharel/skills' -Force | Out-Null
    Dire "Mise $a jour automatique : t${ac}che planifi${e}e gharel-skills, chaque jour (SKILLS_AUTO=0 pour la retirer)."
  }
  function RetirerTache {
    if (-not $windows) { return }
    try {
      if (Get-ScheduledTask -TaskName 'gharel-skills' -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName 'gharel-skills' -Confirm:$false
        Dire "T${ac}che planifi${e}e gharel-skills retir${e}e."
      }
    } catch { Dire "T${ac}che planifi${e}e : $($_.Exception.Message)" }
    $local = Chemin $etat 'installer.ps1'
    if (Test-Path -LiteralPath $local) { Remove-Item -LiteralPath $local -Force }
  }

  # ── Désinstallation ──
  if ($env:SKILLS_ACTION -eq 'desinstaller') {
    if (-not (Test-Path -LiteralPath $manifeste)) { Dire "Aucune installation gharel/skills dans $canonique."; return }
    foreach ($l in $ancien.liens) {
      if ((EstLien $l.Chemin) -or (ANous $l.Chemin @($l.Chemin))) { Supprimer $l.Chemin }
    }
    foreach ($nom in @($ancien.skills.Keys)) { Supprimer (Chemin $canonique $nom) }
    foreach ($b in $ancien.sauvegardes) {
      if ((Existe $b.Copie) -and -not (Existe $b.Origine)) {
        Move-Item -LiteralPath $b.Copie -Destination $b.Origine
        Dire "  Restaur${e} : $($b.Origine)"
      }
    }
    if ($ancien.auto -eq '1') { RetirerTache }
    foreach ($p in @($manifeste, $tmp, (Chemin $etat 'installer.ps1'))) { Supprimer $p }
    $sauvegardes = Chemin $etat 'sauvegardes'
    if ((Existe $sauvegardes) -and -not (Get-ChildItem -LiteralPath $sauvegardes -Force)) { Supprimer $sauvegardes }
    foreach ($p in @($etat, $canonique)) {
      if ((Existe $p) -and -not (Get-ChildItem -LiteralPath $p -Force)) { Supprimer $p }
    }
    Dire ("{0} skill(s) d${e}sinstall${e}(s) de {1}." -f $ancien.skills.Count, $canonique)
    return
  }
  if ($env:SKILLS_ACTION) { throw "SKILLS_ACTION inconnue : $env:SKILLS_ACTION (seule valeur : desinstaller)." }

  # ── Sélection : variables d'environnement, sinon celle de la dernière fois ──
  $texteSkills = $ancien.skillsChoisis
  if ($env:SKILLS) { $texteSkills = $env:SKILLS }
  if ($texteSkills -eq 'tout') { $texteSkills = '' }
  $texteCategories = $ancien.categories
  if ($env:SKILLS_CATEGORIE) { $texteCategories = $env:SKILLS_CATEGORIE }
  if ($texteCategories -eq 'tout') { $texteCategories = '' }
  $choixSkills = @(Liste $texteSkills)
  $choixCategories = @(Liste $texteCategories)

  try {
    Dire "gharel/skills : lecture du catalogue$pp"
    New-Item -ItemType Directory -Force -Path $canonique, $etat | Out-Null
    Supprimer $tmp
    New-Item -ItemType Directory -Path $tmp | Out-Null
    $fichierIndex = Chemin $tmp 'skills.tsv'
    Invoke-WebRequest -Uri ($site + 'skills.tsv') -OutFile $fichierIndex -UseBasicParsing
    $catalogue = @(foreach ($ligne in Get-Content -LiteralPath $fichierIndex -Encoding UTF8) {
        if (-not $ligne -or $ligne.StartsWith('#')) { continue }
        $c = $ligne -split "`t"
        $remplace = ''
        if ($c[4] -ne '-') { $remplace = $c[4] }
        [pscustomobject]@{ Nom = $c[0]; Categorie = $c[1]; Version = $c[2]; Statut = $c[3]; RemplacePar = $remplace }
      })
    foreach ($nom in $choixSkills) {
      if (-not ($catalogue | Where-Object { $_.Nom -eq $nom })) { Dire "  ? $nom : skill inconnu du catalogue." }
    }

    # Skills voulus : recommandés (ou nommés dans SKILLS), dépréciés s'ils sont déjà là, jamais retirés.
    $voulus = @(foreach ($s in $catalogue) {
        if ($s.Statut -eq 'retire') { continue }
        if ($choixCategories.Count -and $choixCategories -notcontains $s.Categorie) { continue }
        if ($choixSkills.Count) { if ($choixSkills -contains $s.Nom) { $s }; continue }
        if ($s.Statut -eq 'recommande' -or ($s.Statut -eq 'deprecie' -and $ancien.skills.ContainsKey($s.Nom))) { $s }
      })
    if (-not $voulus.Count) { throw "Aucun skill ne correspond $a la s${e}lection." }
    $nomsVoulus = @($voulus | ForEach-Object { $_.Nom })
    $connus = @($ancien.skills.Keys | ForEach-Object { Chemin $canonique $_ }) + @($ancien.liens | ForEach-Object { $_.Chemin })
    $sauvegardes = New-Object System.Collections.ArrayList
    foreach ($b in $ancien.sauvegardes) { [void]$sauvegardes.Add($b) }
    function Sauvegarder($chemin) {
      $dossier = Chemin $etat 'sauvegardes'
      New-Item -ItemType Directory -Force -Path $dossier | Out-Null
      $copie = Chemin $dossier ((Split-Path $chemin -Leaf) + '-' + (Get-Date -Format 'yyyyMMddHHmmss'))
      Move-Item -LiteralPath $chemin -Destination $copie
      [void]$sauvegardes.Add(@{ Origine = $chemin; Copie = $copie })
      Dire "  ! $chemin n'est pas un skill gharel/skills : sauvegard${e} dans $copie"
    }

    # ── Copies dans ~/.agents/skills : seulement les skills nouveaux ou changés ──
    $bilan = New-Object System.Collections.ArrayList
    foreach ($s in $voulus) {
      $dest = Chemin $canonique $s.Nom
      $avant = $ancien.skills[$s.Nom]
      if ($avant -eq $s.Version -and (Test-Path -LiteralPath (Chemin $dest 'SKILL.md'))) {
        [void]$bilan.Add("  = $($s.Nom) $($s.Version)")
      } else {
        $zip = Chemin $tmp ($s.Nom + '.zip')
        Invoke-WebRequest -Uri ($site + 'telechargements/' + $s.Nom + '.zip') -OutFile $zip -UseBasicParsing
        $extrait = Chemin $tmp $s.Nom
        Expand-Archive -LiteralPath $zip -DestinationPath $extrait -Force
        if (Existe $dest) { if (ANous $dest $connus) { Supprimer $dest } else { Sauvegarder $dest } }
        Move-Item -LiteralPath (Chemin $extrait $s.Nom) -Destination $dest
        if ($avant) { [void]$bilan.Add("  ^ $($s.Nom) $avant -> $($s.Version)") }
        else { [void]$bilan.Add("  + $($s.Nom) $($s.Version)") }
      }
      if ($s.Statut -eq 'deprecie') {
        $suite = ''
        if ($s.RemplacePar) { $suite = ", remplac${e} par $($s.RemplacePar)" }
        [void]$bilan.Add("    $($s.Nom) est d${e}pr${e}ci${e}$suite.")
      }
    }
    foreach ($nom in @($ancien.skills.Keys)) {
      if ($nomsVoulus -contains $nom) { continue }
      Supprimer (Chemin $canonique $nom)
      $raison = "hors s${e}lection"
      $entree = $catalogue | Where-Object { $_.Nom -eq $nom }
      if (-not $entree -or $entree.Statut -eq 'retire') { $raison = "retir${e} du catalogue" }
      [void]$bilan.Add("  - $nom ($raison)")
    }

    # ── Jonctions pour les assistants qui ne lisent pas ~/.agents/skills ──
    $fichierPlugins = Chemin $accueil '.claude' 'plugins' 'installed_plugins.json'
    $plugin = (Test-Path -LiteralPath $fichierPlugins) -and
      [bool](Select-String -LiteralPath $fichierPlugins -SimpleMatch '@gharel-skills"' -Quiet)
    $cibles = @()
    if (-not $env:SKILLS_DOSSIER) {
      foreach ($as in $assistants) {
        if (-not $as.Lien) { continue }
        if (-not (Test-Path -LiteralPath (Chemin $accueil ($as.Signe -split '/')))) { continue }
        if ($as.Nom -eq 'Claude Code' -and $plugin) { continue }
        $cibles += , @{ Nom = $as.Nom; Dossier = (Chemin $accueil ($as.Lien -split '/')) }
      }
    }
    foreach ($l in $ancien.liens) {
      if ((EstLien $l.Chemin) -or (ANous $l.Chemin @($l.Chemin))) { Supprimer $l.Chemin }
    }
    $typeLien = 'SymbolicLink'
    if ($windows) { $typeLien = 'Junction' }
    $liens = New-Object System.Collections.ArrayList
    $lignesLiens = New-Object System.Collections.ArrayList
    foreach ($cible in $cibles) {
      New-Item -ItemType Directory -Force -Path $cible.Dossier | Out-Null
      $copies = 0
      foreach ($s in $voulus) {
        $lien = Chemin $cible.Dossier $s.Nom
        if (Existe $lien) {
          if ((EstLien $lien) -or (ANous $lien $connus)) { Supprimer $lien } else { Sauvegarder $lien }
        }
        try {
          New-Item -ItemType $typeLien -Path $lien -Target (Chemin $canonique $s.Nom) -ErrorAction Stop | Out-Null
        } catch {
          Copy-Item -LiteralPath (Chemin $canonique $s.Nom) -Destination $lien -Recurse
          $copies++
        }
        [void]$liens.Add(@{ Nom = $s.Nom; Chemin = $lien })
      }
      $forme = 'jonctions'
      if (-not $windows) { $forme = 'liens' }
      if ($copies) { $forme = "copies (liens refus${e}s)" }
      [void]$lignesLiens.Add("  $($cible.Nom) : $forme dans $($cible.Dossier)")
    }

    # ── Copies en double laissées par les anciennes versions de l'installeur ──
    $nettoyes = 0
    if (-not $env:SKILLS_DOSSIER) {
      $dossiers = @($anciennesCibles)
      if ($plugin) { $dossiers += '.claude/skills' }
      foreach ($rel in $dossiers) {
        foreach ($s in $catalogue) {
          $p = Chemin $accueil ($rel -split '/') $s.Nom
          if ((Existe $p) -and -not (EstLien $p) -and (ANous $p @())) { Supprimer $p; $nettoyes++ }
        }
      }
    }

    # ── Mise à jour automatique ──
    $auto = $ancien.auto
    if ($env:SKILLS_AUTO -eq '1') { $auto = '1'; InscrireTache $false }
    elseif ($env:SKILLS_AUTO -eq '0') { $auto = '0'; RetirerTache }
    elseif ($env:SKILLS_AUTO -eq 'essai') { InscrireTache $true }
    elseif ($auto -eq '1' -and $windows) {
      # La tâche lance la copie locale de l'installeur : on la rafraîchit à chaque passage.
      Invoke-WebRequest -Uri ($site + 'installer.ps1') -OutFile (Chemin $etat 'installer.ps1') -UseBasicParsing
    }

    # ── Nouveau manifeste ──
    $lignes = New-Object System.Collections.ArrayList
    [void]$lignes.Add('# gharel/skills : manifeste tenu par installer.ps1 (ne pas modifier)')
    [void]$lignes.Add("selection`tskills`t" + ($choixSkills -join ','))
    [void]$lignes.Add("selection`tcategories`t" + ($choixCategories -join ','))
    [void]$lignes.Add("auto`t$auto")
    foreach ($s in $voulus) { [void]$lignes.Add("skill`t$($s.Nom)`t$($s.Version)") }
    foreach ($l in $liens) { [void]$lignes.Add("lien`t$($l.Nom)`t$($l.Chemin)") }
    foreach ($b in $sauvegardes) { if (Existe $b.Copie) { [void]$lignes.Add("sauvegarde`t$($b.Origine)`t$($b.Copie)") } }
    [IO.File]::WriteAllLines($manifeste, [string[]] $lignes)

    # ── Bilan ──
    Dire ("{0} skill(s) dans {1}" -f $voulus.Count, $canonique)
    foreach ($ligne in $bilan) { Dire $ligne }
    $lecteurs = @($assistants | Where-Object { -not $_.Lien -and (Test-Path -LiteralPath (Chemin $accueil ($_.Signe -split '/'))) } |
        ForEach-Object { $_.Nom })
    if (-not $env:SKILLS_DOSSIER) {
      if ($lecteurs.Count) { Dire ("  Lu par : " + ($lecteurs -join ', ') + '.') }
      else { Dire '  Lu par Codex, Gemini CLI, GitHub Copilot, Cursor et OpenCode.' }
    }
    foreach ($ligne in $lignesLiens) { Dire $ligne }
    if ($plugin) { Dire "  Claude Code : plugin gharel-skills install${e}, mis ${a} jour par /plugin marketplace update gharel-skills." }
    if ($nettoyes) { Dire "  $nettoyes ancienne(s) copie(s) en double retir${e}e(s)." }
    $lxss = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss'
    if ($windows -and -not $env:SKILLS_DEPUIS_WSL -and -not $env:SKILLS_DOSSIER -and (Test-Path $lxss) -and
      @(Get-ChildItem $lxss -ErrorAction SilentlyContinue).Count) {
      Dire "  WSL : lancez aussi  curl -fsSL ${site}installer.sh | sh  dans votre distribution."
    }
    if ($auto -ne '1') { Dire "Relancez cette commande pour mettre $a jour, ou ajoutez `$env:SKILLS_AUTO='1' pour le faire chaque jour." }
    Dire "Catalogue : $site"
  } finally {
    Supprimer $tmp
  }
} ($args -contains '-silencieux' -or $env:SKILLS_SILENCIEUX -eq '1')
