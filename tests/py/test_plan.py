import io
import json

from conftest import SKILLS

import rendre_plan as r

EXEMPLE = SKILLS / "skazy-plan-formation" / "exemples" / "plan-exemple.json"


def plan(**modifs):
    donnees = json.loads(EXEMPLE.read_text(encoding="utf-8"))
    donnees.update(modifs)
    return r.normaliser_plan(donnees)


def texte_tableaux(partie):
    return " ".join(c.text for t in partie.tables for rangee in t.rows for c in rangee.cells)


def test_exemple_valide_sans_avertissement():
    p, rapport = plan()
    assert rapport.erreurs == []
    assert rapport.avertissements == []
    assert p["_cat"]["nom"] == "Bureautique"
    assert p["_modalites"]["tarif"] == "Sur devis"


def test_erreurs_et_avertissements():
    _, rapport = plan(categorie="Cuisine")
    assert any("Catégorie inconnue" in e for e in rapport.erreurs)
    _, rapport = plan(description="Cette formation présente Excel.", objectifs=["Comprendre Excel"])
    textes = " ".join(rapport.avertissements)
    assert "Cette formation" in textes
    assert "peu observable" in textes
    assert "1 objectifs" in textes


def test_debordement_signale():
    point = "Un point assez long pour occuper toute une ligne du programme"
    longs = [{"titre": "Partie {}".format(i), "points": [point] * 6} for i in range(8)]
    _, rapport = plan(programme=longs)
    assert any("dépasse" in a for a in rapport.avertissements)


def test_html_reprend_le_modele():
    p, _ = plan()
    html = r.rendre_html(p)
    assert "--c:#A977DA" in html
    assert "Excel : les bases" in html.replace(" ", " ")
    assert 'class="page p2"' in html
    assert "RIDET" in html
    assert "<strong>Créer</strong>" in html


def test_html_une_seule_page_sans_modalites():
    p, _ = plan(modalites=False)
    assert 'class="page p2"' not in r.rendre_html(p)


def test_docx_entetes_et_pieds():
    from docx import Document

    p, _ = plan()
    doc = Document(io.BytesIO(r.rendre_docx(p)))
    section = doc.sections[0]
    assert section.different_first_page_header_footer
    assert "Excel" in texte_tableaux(section.first_page_header)
    assert "Initiation" in texte_tableaux(section.first_page_header)
    assert "formation@skazy.nc" in texte_tableaux(section.first_page_footer)
    assert "Modalités et infos pratiques" in texte_tableaux(section.header)
    assert "RIDET" in texte_tableaux(section.footer)
    assert section.left_margin == 0
    assert section.top_margin == 0
    corps = " ".join(par.text for par in doc.paragraphs)
    assert "Prenez en main Excel" in corps
