import base64
import io
import json
import re
import zipfile

from conftest import SKILLS

import docx_google_docs as g
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
    assert "MODALITÉS ET INFOS PRATIQUES" in texte_tableaux(section.header)
    assert "RIDET" in texte_tableaux(section.footer)
    assert section.left_margin == 0
    assert section.top_margin == 0
    corps = " ".join(par.text for par in doc.paragraphs)
    assert "Prenez en main Excel" in corps


def test_docx_pret_pour_google_docs():
    p, _ = plan()
    donnees = r.rendre_docx(p)
    assert len(donnees) < 30_000
    z = zipfile.ZipFile(io.BytesIO(donnees))
    noms = z.namelist()
    assert not any(n.startswith(("customXml/", "word/fonts/")) or "stylesWithEffects" in n or "thumbnail" in n for n in noms)
    xml = "".join(z.read(n).decode("utf-8") for n in noms if n.endswith(".xml"))
    assert 'w:lineRule="exact"' not in xml and "<w:caps" not in xml and "latentStyles" not in xml
    defauts = re.search(r"<w:docDefaults>.*?</w:docDefaults>", z.read("word/styles.xml").decode("utf-8"), re.S).group(0)
    assert 'w:ascii="Raleway"' in defauts and 'w:val="fr-FR"' in defauts
    assert g.plus_long_repete(base64.b64encode(donnees).decode())[0] <= 40
    # Mises en page que Google Docs lit comme Word : voir references/google-docs.md.
    assert not re.search(r'<w:tcMar>(?:(?!</w:tcMar>).)*<w:left w:w="[1-9]', xml)
    for partie in ("word/header1.xml", "word/header2.xml"):
        entete = z.read(partie).decode("utf-8")
        assert entete.index("<w:p>") < entete.index("<w:tbl>") or entete.index("<w:p ") < entete.index("<w:tbl>")
        for rangee in re.findall(r"<w:tr[ >].*?</w:tr>", entete, re.S):
            assert len(set(re.findall(r'<w:top w:w="(\d+)"', rangee))) <= 1


def test_preparer_un_docx_venu_de_word():
    from docx import Document
    from docx.shared import Pt
    from PIL import Image

    doc = Document()
    par = doc.add_paragraph()
    run = par.add_run("Titre")
    run.font.size = Pt(20)
    par.paragraph_format.line_spacing = Pt(30)  # interligne exact
    image = io.BytesIO()
    Image.new("RGB", (1200, 600), "#A977DA").save(image, "PNG")
    doc.add_paragraph().add_run().add_picture(io.BytesIO(image.getvalue()), width=Pt(72))
    tampon = io.BytesIO()
    doc.save(tampon)
    # Police embarquée, comme Word l'écrit.
    source = zipfile.ZipFile(io.BytesIO(tampon.getvalue()))
    fichiers = {n: source.read(n) for n in source.namelist()}
    fichiers["word/fonts/font1.odttf"] = b"0" * 5000
    fichiers["word/_rels/fontTable.xml.rels"] = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/font" Target="fonts/font1.odttf"/></Relationships>'
    )
    fichiers["[Content_Types].xml"] = fichiers["[Content_Types].xml"].replace(
        b"<Default ", b'<Default Extension="odttf" ContentType="application/vnd.openxmlformats-officedocument.obfuscatedFont"/><Default ', 1
    )
    avec_police = io.BytesIO()
    with zipfile.ZipFile(avec_police, "w") as z:
        for n, v in fichiers.items():
            z.writestr(n, v)

    resultat, messages = g.preparer_docx(avec_police.getvalue())
    z = zipfile.ZipFile(io.BytesIO(resultat))
    assert not any(n.startswith("word/fonts/") for n in z.namelist())
    assert b"odttf" not in z.read("[Content_Types].xml") and b"odttf" not in z.read("word/_rels/fontTable.xml.rels")
    document = z.read("word/document.xml").decode("utf-8")
    attendu = round(240 * 30 / (20 * g.HAUTEUR_LIGNE))
    assert 'w:line="{}" w:lineRule="auto"'.format(attendu) in document or 'w:lineRule="auto" w:line="{}"'.format(attendu) in document
    media = [n for n in z.namelist() if n.startswith("word/media/")]
    assert media == ["word/media/0.png"]
    assert Image.open(io.BytesIO(z.read(media[0]))).width <= 110 + 8
    assert any("interligne" in m for m in messages)
    Document(io.BytesIO(resultat))  # le fichier reste lisible
