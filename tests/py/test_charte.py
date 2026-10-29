"""Lecture de la charte : dans design-skazy, sinon dans l'export que le .zip embarque ; jamais ses modèles."""

import hashlib
import json
import shutil

import pytest

import charte as ch

PLAN = "skazy-plan-formation"


def design_factice(tmp_path):
    """Dépôt design-skazy minimal : export de la charte et modèle du plan."""
    d = tmp_path / "design-skazy"
    (d / "charte").mkdir(parents=True)
    charte = json.loads(ch.fichier_charte("charte.json").read_text(encoding="utf-8"))
    charte["contact"]["site"] = "design.exemple"
    (d / "charte" / "charte.json").write_text(json.dumps(charte), encoding="utf-8")
    (d / "charte" / "plan-formation.css").write_text("/* design */", encoding="utf-8")
    (d / "charte" / "plan-formation.js").write_text("// design", encoding="utf-8")
    gabarit = d / "templates" / "plan-formation" / "PlanFormation.dc.html"
    gabarit.parent.mkdir(parents=True)
    gabarit.write_text("<modèle>", encoding="utf-8")
    return d, hashlib.sha256(gabarit.read_bytes()).hexdigest()


def charte_du_skill(tmp_path, empreinte=None, embarquee=True, feuilles=True):
    """assets/charte d'un skill, aligné sur l'empreinte donnée : celui du .zip (export de design-skazy
    embarqué), ou celui du dépôt (embarquee=False : alignement seulement)."""
    dossier = tmp_path / "skill"
    dossier.mkdir()
    noms = ["charte.json", "logo-color.png"] + (["plan-formation.css", "plan-formation.js"] if feuilles else [])
    for nom in noms if embarquee else []:
        shutil.copy(ch.fichier_charte(nom), dossier / nom)
    if empreinte:
        (dossier / "alignement.json").write_text(json.dumps({"modeles": {"plan-formation": {"empreinte": empreinte}}}), encoding="utf-8")
    return dossier


def test_le_depot_ne_garde_aucune_copie_de_la_charte():
    for nom in ch.EXPORT.values():
        assert not (ch.DOSSIER_CHARTE / nom).exists()
    assert ch.DESIGN and ch.fichier_charte("charte.json") == ch.DESIGN / "charte" / "charte.json"


def test_export_de_design_skazy_si_le_modele_est_aligne(tmp_path):
    design, empreinte = design_factice(tmp_path)
    skill = charte_du_skill(tmp_path, empreinte)
    avant = sorted(f.name for f in skill.iterdir())
    sources, avertissements = ch.sources_charte(design, skill, PLAN)
    assert avertissements == []
    assert sources["charte.json"] == design / "charte" / "charte.json"
    assert sources["plan-formation.css"] == design / "charte" / "plan-formation.css"
    assert sources["logo-color.png"] == skill / "logo-color.png"  # absent de design-skazy : celui du .zip
    assert sorted(f.name for f in skill.iterdir()) == avant  # rien n'est copié dans le skill


def test_skill_du_depot_lit_tout_dans_design_skazy(tmp_path):
    design, empreinte = design_factice(tmp_path)
    skill = charte_du_skill(tmp_path, empreinte, embarquee=False)
    sources, avertissements = ch.sources_charte(design, skill, PLAN)
    assert avertissements == []
    assert sources == {
        "charte.json": design / "charte" / "charte.json",
        "plan-formation.css": design / "charte" / "plan-formation.css",
        "plan-formation.js": design / "charte" / "plan-formation.js",
    }


def test_modele_change_garde_la_feuille_alignee_du_zip(tmp_path):
    design, _ = design_factice(tmp_path)
    skill = charte_du_skill(tmp_path, "ancienne-empreinte")
    sources, avertissements = ch.sources_charte(design, skill, PLAN)
    assert sources["charte.json"] == design / "charte" / "charte.json"  # les données restent à jour
    assert sources["plan-formation.css"] == skill / "plan-formation.css"
    assert sources["plan-formation.js"] == skill / "plan-formation.js"
    assert len(avertissements) == 1 and "plan-formation" in avertissements[0] and "alignée" in avertissements[0]


def test_modele_change_sans_zip_prend_la_nouvelle_feuille_et_avertit(tmp_path):
    design, _ = design_factice(tmp_path)
    skill = charte_du_skill(tmp_path, "ancienne-empreinte", embarquee=False)
    sources, avertissements = ch.sources_charte(design, skill, PLAN)
    assert sources["plan-formation.css"] == design / "charte" / "plan-formation.css"
    assert len(avertissements) == 1 and "npm run modeles" in avertissements[0]


def test_skill_sans_modele_sans_avertissement(tmp_path):
    design, _ = design_factice(tmp_path)
    (design / "templates" / "plan-formation" / "PlanFormation.dc.html").write_text("<autre>", encoding="utf-8")
    skill = charte_du_skill(tmp_path, feuilles=False)
    sources, avertissements = ch.sources_charte(design, skill, "skazy-quiz")
    assert avertissements == []
    assert sources["charte.json"] == design / "charte" / "charte.json"


def test_sans_design_skazy_l_export_du_zip(tmp_path, monkeypatch):
    skill = charte_du_skill(tmp_path, "x")
    sources, avertissements = ch.sources_charte(None, skill, PLAN)
    assert avertissements == [] and sources["charte.json"] == skill / "charte.json"
    monkeypatch.setenv("DESIGN_SKAZY", "0")
    assert ch.trouver_design() is None
    design, _ = design_factice(tmp_path)
    monkeypatch.setenv("DESIGN_SKAZY", str(design))
    assert ch.trouver_design() == design


def test_sans_design_skazy_ni_zip_un_message_clair(tmp_path, monkeypatch):
    sources, _ = ch.sources_charte(None, tmp_path / "absent", PLAN)
    assert sources == {}
    monkeypatch.setattr(ch, "SOURCES", sources)
    with pytest.raises(SystemExit, match="DESIGN_SKAZY"):
        ch.fichier_charte("charte.json")
