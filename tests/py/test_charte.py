"""Synchronisation de la charte au lancement : l'export de design-skazy l'emporte, jamais ses modèles."""

import hashlib
import json
import shutil

import charte as ch


def design_factice(tmp_path):
    """Dépôt design-skazy minimal : export de la charte et modèle du plan."""
    d = tmp_path / "design-skazy"
    (d / "charte").mkdir(parents=True)
    charte = json.loads((ch.DOSSIER_CHARTE / "charte.json").read_text(encoding="utf-8"))
    charte["contact"]["site"] = "design.exemple"
    (d / "charte" / "charte.json").write_text(json.dumps(charte), encoding="utf-8")
    (d / "charte" / "plan-formation.css").write_text("/* design */", encoding="utf-8")
    (d / "charte" / "plan-formation.js").write_text("// design", encoding="utf-8")
    gabarit = d / "templates" / "plan-formation" / "PlanFormation.dc.html"
    gabarit.parent.mkdir(parents=True)
    gabarit.write_text("<modèle>", encoding="utf-8")
    return d, hashlib.sha256(gabarit.read_bytes()).hexdigest()


def charte_du_skill(tmp_path, empreinte=None, feuilles=True):
    """Copie de assets/charte d'un skill, alignée sur l'empreinte donnée."""
    dossier = tmp_path / "skill"
    dossier.mkdir()
    noms = ["charte.json", "logo-color.png"] + (["plan-formation.css", "plan-formation.js"] if feuilles else [])
    for nom in noms:
        shutil.copy(ch.DOSSIER_CHARTE / nom, dossier / nom)
    if empreinte:
        (dossier / "alignement.json").write_text(json.dumps({"modeles": {"plan-formation": {"empreinte": empreinte}}}), encoding="utf-8")
    return dossier


def test_export_de_design_skazy_si_le_modele_est_aligne(tmp_path):
    design, empreinte = design_factice(tmp_path)
    skill = charte_du_skill(tmp_path, empreinte)
    avant = sorted(f.name for f in skill.iterdir())
    sources, avertissements = ch.sources_charte(design, skill)
    assert avertissements == []
    assert sources["charte.json"] == design / "charte" / "charte.json"
    assert sources["plan-formation.css"] == design / "charte" / "plan-formation.css"
    assert sources["logo-color.png"] == skill / "logo-color.png"  # absent de design-skazy : copie du skill
    assert sorted(f.name for f in skill.iterdir()) == avant  # rien n'est copié dans le skill


def test_modele_change_garde_la_feuille_alignee(tmp_path):
    design, _ = design_factice(tmp_path)
    skill = charte_du_skill(tmp_path, "ancienne-empreinte")
    sources, avertissements = ch.sources_charte(design, skill)
    assert sources["charte.json"] == design / "charte" / "charte.json"  # les données restent à jour
    assert sources["plan-formation.css"] == skill / "plan-formation.css"
    assert sources["plan-formation.js"] == skill / "plan-formation.js"
    assert len(avertissements) == 1 and "plan-formation" in avertissements[0]


def test_skill_sans_modele_sans_avertissement(tmp_path):
    design, _ = design_factice(tmp_path)
    (design / "templates" / "plan-formation" / "PlanFormation.dc.html").write_text("<autre>", encoding="utf-8")
    skill = charte_du_skill(tmp_path, feuilles=False)
    sources, avertissements = ch.sources_charte(design, skill)
    assert avertissements == []
    assert sources["charte.json"] == design / "charte" / "charte.json"


def test_sans_design_skazy_la_copie_du_skill(tmp_path, monkeypatch):
    skill = charte_du_skill(tmp_path, "x")
    sources, avertissements = ch.sources_charte(None, skill)
    assert avertissements == [] and sources["charte.json"] == skill / "charte.json"
    monkeypatch.setenv("DESIGN_SKAZY", "0")
    assert ch.trouver_design() is None
    design, _ = design_factice(tmp_path)
    monkeypatch.setenv("DESIGN_SKAZY", str(design))
    assert ch.trouver_design() == design
