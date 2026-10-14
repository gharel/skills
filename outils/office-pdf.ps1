# Convertit un DOCX (Word) ou un PPTX (PowerPoint) en PDF pour le contrôle visuel des rendus (Windows).
# Usage : pwsh outils/office-pdf.ps1 fichier.docx|fichier.pptx sortie.pdf
# Si l'automatisation COM refuse de démarrer (erreur 0x80080005), l'application est d'abord lancée
# en mode /automation, puis on s'y connecte.
param([string]$Source, [string]$Sortie)
$ErrorActionPreference = 'Stop'
$Source = (Resolve-Path $Source).Path
$Sortie = [System.IO.Path]::GetFullPath($Sortie)
$office = 'C:\Program Files\Microsoft Office\root\Office16'

function Ouvrir([string]$progId, [string]$exe) {
  try { return New-Object -ComObject $progId } catch {
    Start-Process -FilePath (Join-Path $office $exe) -ArgumentList '/automation', '-Embedding'
    Start-Sleep -Seconds 8
    return New-Object -ComObject $progId
  }
}

if ($Source.EndsWith('.docx')) {
  $word = Ouvrir 'Word.Application' 'WINWORD.EXE'
  $word.Visible = $false
  $doc = $word.Documents.Open($Source, $false, $true)
  $doc.ExportAsFixedFormat($Sortie, 17)
  Write-Output ("{0} page(s)" -f $doc.ComputeStatistics(2))
  $doc.Close($false)
} elseif ($Source.EndsWith('.pptx')) {
  $ppt = Ouvrir 'PowerPoint.Application' 'POWERPNT.EXE'
  $pres = $ppt.Presentations.Open($Source, $true, $false, $false)
  $pres.SaveAs($Sortie, 32)
  Write-Output ("{0} slide(s)" -f $pres.Slides.Count)
  $pres.Close()
}
Write-Output $Sortie
