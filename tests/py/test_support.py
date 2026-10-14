import io
import json

from conftest import SKILLS

import charte as ch
import support_modele as m

EXEMPLE = SKILLS / "skazy-support-formation" / "exemples" / "support-exemple.json"


def support(**modifs):
    donnees = json.loads(EXEMPLE.read_text(encoding="utf-8"))
    donnees.update(modifs)
    return m.normaliser_support(donnees)


def test_exemple_couvre_les_30_mises_en_page():
    s, rapport = support()
    assert rapport.erreurs == []
    assert {x["type"] for x in s["_slides"]} == set(m.TYPES)


def test_quiz_en_deux_slides_et_numerotation():
    s, _ = support()
    quiz = [x for x in s["_slides"] if x["type"] == "quiz"]
    assert len(quiz) == 4
    assert [q["_reponse"] for q in quiz] == [False, True, False, True]
    assert (quiz[0]["numero"], quiz[0]["total"]) == (1, 2)
    assert [x["numero"] for x in s["_slides"] if x["type"] == "chapitre"] == [1, 2, 3]


def test_erreurs():
    slides = [{"type": "inconnu"}, {"type": "quiz", "question": "?", "propositions": ["a", "b"], "bonne": 5}]
    _, rapport = support(slides=slides)
    textes = " ".join(rapport.erreurs)
    assert "type inconnu" in textes
    assert "bonne" in textes


def test_alias_et_lettre_de_reponse():
    slides = [
        {"type": "couverture"},
        {"type": "Chiffre clé", "chiffre": "3", "phrase": "x"},
        {"type": "quiz", "question": "?", "propositions": ["a", "b"], "bonne": "B"},
    ]
    s, rapport = support(slides=slides)
    assert rapport.erreurs == []
    assert s["_slides"][1]["type"] == "chiffre-cle"
    assert s["_slides"][2]["bonne"] == 1


def test_html():
    from support_html import rendre_html

    s, _ = support()
    html = rendre_html(s)
    assert html.count('<section class="slide"') == len(s["_slides"])
    assert 'template class="notes-slide"' in html
    assert "--c:#A977DA" in html


def test_pptx_slides_notes_et_pied():
    from pptx import Presentation
    from support_pptx import rendre_pptx

    ch.IMAGES_LOCALES.clear()
    s, _ = support()
    prs = Presentation(io.BytesIO(rendre_pptx(s)))
    assert len(prs.slides) == len(s["_slides"])
    assert prs.slide_width == 12192000
    notes = [sl.notes_slide.notes_text_frame.text for sl in prs.slides if sl.has_notes_slide]
    assert any("Accueil des participants" in n for n in notes)
    textes = " ".join(sh.text_frame.text for sh in prs.slides[1].shapes if sh.has_text_frame)
    assert "Excel : les bases" in textes.replace(" ", " ")
    assert "02" in textes
