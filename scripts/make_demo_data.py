#!/usr/bin/env python3
"""
Build the data for the three-minute demo (Vision/Demo in drei Minuten.md), fresh on every run.

    python3 scripts/make_demo_data.py <target> [--templates <folder with Standard>]

Under target:
- Templates/Standard - copied from --templates (default: MyOS_Test/Templates, else ~/Templates),
  without access rights (ACLs.md).
- Downloads - about 30 mixed files, the mess of scene 1, and "Rechnung Heizung 2025.odt" for
  scene 5 (LibreOffice saves it through the "Perspektiven" drive).
- Projekte - the projects root: "Urlaub 2025" an ordinary folder (scene 2 makes it a project);
  Familie, Job and Auto projects whose 04_Finanz holds invoices (born the way MyOS bears
  folders, so the lens has something to show); Wohnen a project without 04_Finanz.

Scope started in target/Projekte puts the drive "Perspektiven" next to it.

A target that exists must be an earlier demo (it holds the marker file .myos-demo): it is
rebuilt. Anything else is refused, and so is a demo whose drive is still mounted.

Needs Pillow and reportlab; LibreOffice (soffice) for the .odt, which is left out without it.
"""

import argparse
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.make_tutorial_data import write_pdf, write_photo  # noqa: E402

MARKER = ".myos-demo"

# A document: (file name, kind, content) as in make_tutorial_data: pdf (sender, title, lines,
# items as (what, amount) or None), photo (scene), note (Markdown).

DOWNLOADS = [
    ("Rechnung_2025-03_8812.pdf", "pdf", ("Stadtwerke Mitte", "Stromrechnung März 2025",
                                          ["Kundennummer 40-118812"], [("Strom März", "84,20")])),
    ("Rechnung (1).pdf", "pdf", ("Elektro Huber", "Rechnung 2025-117",
                                 ["Tausch Steckdosen Küche"], [("Arbeit 2 h", "128,00"), ("Material", "36,40")])),
    ("Rechnung (2).pdf", "pdf", ("Optik Klar", "Rechnung 77310", ["Brille, Gläser neu"], [("Gläser", "240,00")])),
    ("scan0003.pdf", "pdf", ("Finanzamt", "Einkommensteuerbescheid 2024", ["Gutschrift"], [("Gutschrift", "412,00")])),
    ("scan0004.pdf", "pdf", ("Hausverwaltung Sonnhof", "Betriebskostenabrechnung 2024", ["Wohnung 7"], None)),
    ("Vertrag_final_v2.pdf", "pdf", ("Mobilfunk Plus", "Vertrag Tarif Smart 20", ["Laufzeit 24 Monate"], None)),
    ("Vertrag_final_v3_WIRKLICH.pdf", "pdf", ("Mobilfunk Plus", "Vertrag Tarif Smart 20",
                                              ["Laufzeit 24 Monate, korrigiert"], None)),
    ("Kassenbon Baumarkt.pdf", "pdf", ("Baumarkt Nord", "Kassenbon 0815-22", ["Filiale Süd"],
                                       [("Schrauben", "6,90"), ("Farbe weiß 10 l", "54,00")])),
    ("Zahnarzt Rechnung.pdf", "pdf", ("Dr. Weiß", "Honorarnote 2025-061", ["Mundhygiene"], [("Mundhygiene", "95,00")])),
    ("Kfz-Versicherung 2025.pdf", "pdf", ("Weltweit Versicherung AG", "Prämienvorschreibung 2025",
                                          ["Kennzeichen W-12345A"], [("Haftpflicht und Kasko", "612,00")])),
    ("Gehaltszettel Mai.pdf", "pdf", ("Firma Muster GmbH", "Lohnzettel Mai 2025", ["Personalnummer 118"], None)),
    ("Bestellbestätigung 449-221.pdf", "pdf", ("Versand24", "Bestellung 449-221", ["Lieferung in 3 Tagen"],
                                                [("Wasserkocher", "39,99")])),
    ("Flyer Sommerfest.pdf", "pdf", ("Gemeinde", "Sommerfest am Dorfplatz", ["Samstag, 14. Juni"], None)),
    ("Anleitung Router.pdf", "pdf", ("NetBox", "Kurzanleitung", ["WLAN einrichten"], None)),
    ("IMG_2041.jpg", "photo", "beach"),
    ("IMG_2042.jpg", "photo", "sunset"),
    ("IMG_2107.jpg", "photo", "town"),
    ("IMG_2203.jpg", "photo", "mountains"),
    ("IMG_2204.jpg", "photo", "market"),
    ("Screenshot 2025-04-02.png", "photo", "dinner"),
    ("Notizen.md", "note", "# Notizen\n\n- Steuerberater anrufen\n- Kfz-Pickerl im Juni\n"),
    ("Notizen (Kopie).md", "note", "# Notizen\n\n- Steuerberater anrufen\n"),
    ("Einkaufsliste.md", "note", "# Einkaufsliste\n\n- Milch\n- Brot\n"),
    ("Passwort-Hinweise.md", "note", "# Hinweise\n\nKeine Passwörter hier, nur wo sie stehen.\n"),
    ("Präsentation Q2.pdf", "pdf", ("Firma Muster GmbH", "Quartalsbericht Q2", ["Intern"], None)),
    ("Lebenslauf_neu.pdf", "pdf", ("Lebenslauf", "Lebenslauf", ["Stand 2025"], None)),
    ("Mietvertrag Scan.pdf", "pdf", ("Hausverwaltung Sonnhof", "Mietvertrag Wohnung 7", ["Ab 1.1.2023"], None)),
    ("Reisepass Kopie.pdf", "pdf", ("Kopie", "Reisepass", ["nur für die Buchung"], None)),
    ("Garantie Waschmaschine.pdf", "pdf", ("Haushalt Profi", "Garantieschein", ["5 Jahre"], None)),
    ("Rezept Lasagne.md", "note", "# Lasagne\n\nFür 4 Personen.\n"),
]

URLAUB = [  # an ordinary folder, made a project in scene 2
    ("Hotelrechnung Casa Azul.pdf", "pdf", ("Casa Azul, Lagos", "Rechnung 2025-0815",
                                            ["Aufenthalt 1. bis 14. August 2025"], [("13 Nächte", "1.430,00")])),
    ("Flugbuchung Wien–Faro.pdf", "pdf", ("SkyLine Airways", "Buchungsbestätigung LX7KQ2",
                                          ["Hinflug 1.8.2025, Rückflug 14.8.2025"], None)),
    ("Strand.jpg", "photo", "beach"),
    ("Sonnenuntergang.jpg", "photo", "sunset"),
    ("Reiseideen.md", "note", "# Reiseideen\n\nAlgarve, Anfang August. Mietauto ab Faro.\n"),
]

# Projects: (name, colour, [(folder below the project, documents)]).
PROJECTS = [
    ("Familie", "#d68b39", [
        ("04_Finanz/Ausgaben", [
            ("Stromrechnung 2025.pdf", "pdf", ("Stadtwerke Mitte", "Jahresabrechnung 2025", ["Wohnung 7"],
                                               [("Strom 2025", "1.012,40")])),
            ("Kindergarten Beitrag.pdf", "pdf", ("Kindergarten Regenbogen", "Beitrag September 2025",
                                                 ["Gruppe Igel"], [("Beitrag", "180,00")])),
            ("Zahnarzt Kind.pdf", "pdf", ("Dr. Weiß", "Honorarnote 2025-102", ["Kontrolle"], [("Kontrolle", "45,00")])),
        ]),
        ("04_Finanz/Einnahmen", [
            ("Familienbeihilfe Bescheid.pdf", "pdf", ("Finanzamt", "Mitteilung Familienbeihilfe 2025",
                                                      ["Für ein Kind"], None)),
        ]),
        ("08_Dokumentation/Bilder", [("Geburtstag.jpg", "photo", "dinner")]),
    ]),
    ("Job", "#5b4fd6", [
        ("04_Finanz/Einnahmen", [
            ("Gehaltszettel Jänner.pdf", "pdf", ("Firma Muster GmbH", "Lohnzettel Jänner 2025", ["Personalnummer 118"], None)),
            ("Gehaltszettel Februar.pdf", "pdf", ("Firma Muster GmbH", "Lohnzettel Februar 2025", ["Personalnummer 118"], None)),
        ]),
        ("04_Finanz/Ausgaben", [
            ("Fachbuch.pdf", "pdf", ("Buchhandlung Seite", "Rechnung 3381", ["Fachbuch Projektmanagement"],
                                     [("Fachbuch", "49,90")])),
            ("Fortbildung.pdf", "pdf", ("Akademie Weiter", "Rechnung Kurs 25-09", ["Zwei Tage, Wien"],
                                        [("Kursgebühr", "590,00")])),
        ]),
    ]),
    ("Auto", "#3a8f6a", [
        ("04_Finanz/Ausgaben", [
            ("Service 60.000 km.pdf", "pdf", ("Autohaus Gerade", "Rechnung W-2025-441", ["Service, Ölwechsel"],
                                              [("Service", "289,00"), ("Öl", "64,00")])),
            ("Winterreifen.pdf", "pdf", ("Reifen Rund", "Rechnung 1209", ["4 Winterreifen montiert"],
                                         [("Reifen", "420,00"), ("Montage", "60,00")])),
            ("Versicherung 2025.pdf", "pdf", ("Weltweit Versicherung AG", "Prämie 2025", ["Kennzeichen W-12345A"],
                                              [("Haftpflicht und Kasko", "612,00")])),
        ]),
    ]),
    ("Wohnen", "#4f8fd6", [
        ("", [  # no 04_Finanz: scene 5 bears it
            ("Grundriss.jpg", "photo", "town"),
            ("Einrichtungsideen.md", "note", "# Einrichtung\n\n- Regal fürs Wohnzimmer\n- Lampe im Flur\n"),
        ]),
    ]),
]

HEATING_INVOICE = (
    "<html><body><h1>Rechnung Heizung 2025</h1>"
    "<p>Installateur Warm &amp; Co<br>Rechnung Nr. 2025-0931</p>"
    "<p>Wartung Gastherme, Wohnung 7</p>"
    "<table><tr><td>Wartung</td><td>149,00 €</td></tr>"
    "<tr><td>Dichtung</td><td>12,50 €</td></tr></table></body></html>")


def write_documents(folder, documents):
    folder.mkdir(parents=True, exist_ok=True)
    for name, kind, content in documents:
        path = folder / name
        if kind == "pdf":
            write_pdf(path, content, "de")
        elif kind == "photo":
            write_photo(path, content)
        elif kind == "note":
            path.write_text(content, encoding="utf-8")
        else:
            raise ValueError(f"no such kind: {kind}")


def default_templates():
    for candidate in (REPO_ROOT / "MyOS_Test" / "Templates", Path.home() / "Templates"):
        if (candidate / "Standard").is_dir():
            return candidate
    return None


def _clear(target):
    """Make target empty for a new demo; refuse anything that is not an earlier one."""
    if not target.exists():
        return
    if not (target / MARKER).exists():
        if any(target.iterdir()):
            raise SystemExit(f"{target} is no demo (no {MARKER}) and not empty: not touched")
        return
    drive = target / "Perspektiven"
    if os.path.ismount(drive):
        raise SystemExit(f"The drive {drive} is still mounted: close Scope (and LibreOffice) first")
    shutil.rmtree(target)


def _make_project(folder, colour):
    from core.project import ProjectConfig

    with contextlib.redirect_stdout(io.StringIO()):
        if not ProjectConfig.make_project(folder):
            raise SystemExit(f"Could not make {folder} a project")
    (folder / ".MyOS" / "Project.md").write_text(f"color: {colour}\n", encoding="utf-8")
    (folder / ".MyOS" / "Templates.md").write_text("Standard\n", encoding="utf-8")


def _bear(project, below):
    """The folder below the project, born as MyOS bears it (template content included)."""
    from core.perspective_session import bear_folder

    if not below:
        return project
    with contextlib.redirect_stdout(io.StringIO()):
        return bear_folder(project, below.split("/"))


def write_odt(path, html):
    """The heating invoice as LibreOffice's own document; skipped without LibreOffice."""
    soffice = shutil.which("soffice")
    if soffice is None:
        print("LibreOffice not found: no", path.name, file=sys.stderr)
        return False
    with tempfile.TemporaryDirectory() as work:
        source = Path(work) / (path.stem + ".html")
        source.write_text(html, encoding="utf-8")
        # Its own profile: a LibreOffice already open does not take the conversion over.
        profile = Path(work) / "profile"
        # Read as a text document, not a web page (Writer/Web would make an HTML template).
        subprocess.run([soffice, f"-env:UserInstallation={profile.as_uri()}", "--headless",
                        "--infilter=HTML (StarWriter)", "--convert-to", "odt:writer8",
                        "--outdir", work, str(source)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        shutil.move(str(Path(work) / (path.stem + ".odt")), path)
    return True


def generate(target, templates):
    target = Path(target).expanduser().resolve()
    _clear(target)
    target.mkdir(parents=True, exist_ok=True)
    (target / MARKER).write_text("Built by scripts/make_demo_data.py; rebuilt on every run.\n",
                                 encoding="utf-8")
    # Without access rights: they are not the demo's subject, and rights for people of a test
    # template ("you are not listed in this project") would show a panel and lock actions.
    shutil.copytree(Path(templates) / "Standard", target / "Templates" / "Standard",
                    ignore=shutil.ignore_patterns("ACLs.md", "ACLs-history"))

    root = target / "Projekte"
    # The projects root is the first project: written by hand (making a project needs one above).
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("color: #4422ee\n", encoding="utf-8")
    (root / ".MyOS" / "Templates.md").write_text("Standard\n", encoding="utf-8")
    write_documents(root / "Urlaub 2025", URLAUB)
    for name, colour, folders in PROJECTS:
        project = root / name
        _make_project(project, colour)
        for below, documents in folders:
            write_documents(_bear(project, below), documents)

    downloads = target / "Downloads"
    write_documents(downloads, DOWNLOADS)
    write_odt(downloads / "Rechnung Heizung 2025.odt", HEATING_INVOICE)
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("target", help="Folder for the demo (new, or an earlier demo)")
    parser.add_argument("--templates", help="Folder holding the template Standard")
    args = parser.parse_args(argv)
    templates = Path(args.templates).expanduser() if args.templates else default_templates()
    if templates is None or not (templates / "Standard").is_dir():
        raise SystemExit("No templates found: pass --templates <folder with Standard>")
    target = generate(args.target, templates)
    print(f"Demo ready: start Scope with {target / 'Projekte'}")


if __name__ == "__main__":
    main()
