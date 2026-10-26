#!/usr/bin/env python3
"""
Generate the exercise files of the tutorial (Learning MyOS), German and English.

Lesson 4 lays a vacation's documents loose in its folder to be sorted by hand; lesson 5 has
the same files back in one unsorted folder, to be turned into a project; lesson 7 has another
vacation in a folder, to watch the suggested folders come to life. Lesson 10 has two small
projects with tags of their own, lesson 11 a company with access rights - each with a note of
exercises. Photos are drawn, the
documents are small PDFs, the video a few seconds of a boat - all tiny, and byte for byte the
same on every run, so the committed files can be checked against this script
(scripts/tests/test_make_tutorial_data.py).

    python3 scripts/make_tutorial_data.py [target]   # default: Learning MyOS in the repo

Needs Pillow, reportlab and ffmpeg.
"""

import io
import math
import random
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

REPO_ROOT = Path(__file__).resolve().parents[1]


# --- What the vacations hold, per language -----------------------------------------------
# A document: (file name, kind, content). Kinds: note (Markdown text), pdf (sender, title,
# lines of text, items as (what, amount) or None), photo (scene), video (scene), mail
# (sender, to, subject, date, body).

ALGARVE = {
    "de": [
        ("Reiseideen.md", "note",
         "# Reiseideen Sommer 2026\n\n"
         "- **Portugal, Algarve** – Strände, Klippen, gutes Essen. Anna war schon dort.\n"
         "- Kroatien, Istrien – nah, aber im August sehr voll.\n"
         "- Sardinien – schön, aber die Fähre ist teuer.\n\n"
         "Entscheidung: **Algarve, 1.–14. August.** Flug nach Faro, Auto mieten.\n"),
        ("Angebot Reisebüro Sonnenschein.pdf", "pdf",
         ("Reisebüro Sonnenschein", "Angebot Nr. 2026-0412",
          ["Algarve, 1. bis 14. August 2026, 2 Personen", "Flug Wien–Faro, Hotel Casa Azul in Lagos"],
          [("Flug Wien–Faro und zurück, 2 Personen", "684,00"), ("Hotel Casa Azul, 13 Nächte", "1.430,00"),
           ("Servicegebühr", "45,00")])),
        ("Flugbuchung Wien–Faro.pdf", "pdf",
         ("SkyLine Airways", "Buchungsbestätigung LX7KQ2",
          ["Hinflug: Sa 1.8.2026, Wien 07:15 – Faro 10:05", "Rückflug: Fr 14.8.2026, Faro 18:40 – Wien 23:20",
           "Passagiere: 2 Erwachsene, je 1 Koffer"], None)),
        ("Hotelbestätigung Casa Azul.pdf", "pdf",
         ("Casa Azul, Lagos", "Reservierungsbestätigung",
          ["Anreise 1.8.2026, Abreise 14.8.2026", "Doppelzimmer mit Meerblick, Frühstück inklusive",
           "Kostenlose Stornierung bis 1.7.2026"], None)),
        ("Mietauto Buchung.pdf", "pdf",
         ("RentaCar Faro", "Mietvertrag Nr. 88231",
          ["Abholung Flughafen Faro, 1.8.2026, 10:30", "Kleinwagen, Vollkasko ohne Selbstbehalt"],
          [("Miete 13 Tage", "312,00"), ("Zusatzfahrer", "39,00")])),
        ("Reiseversicherung Polizze.pdf", "pdf",
         ("Weltweit Versicherung AG", "Polizze RV-551203",
          ["Reiseschutz für 2 Personen, 1.8. bis 14.8.2026",
           "Storno, Reisekranken, Gepäck – Selbstbehalt 0 €"], [("Prämie", "89,00")])),
        ("Mail von Anna – Ich komme mit.eml", "mail",
         ("Anna Berger <anna.berger@example.org>", "du@example.org", "Ich komme mit!",
          "Mon, 02 Mar 2026 19:42:00 +0100",
          "Hallo!\n\nIch hab mit dem Chef geredet: Ich bekomme die zwei Wochen frei.\n"
          "Ich komme also mit an die Algarve! Schick mir die Flugdaten, dann buche ich mit.\n\n"
          "Bis bald,\nAnna\n")),
        ("Packliste.md", "note",
         "# Packliste\n\n- [ ] Reisepass\n- [ ] Badesachen\n- [ ] Sonnencreme\n- [ ] Ladekabel\n"
         "- [ ] Wanderschuhe für die Klippen\n- [ ] Führerschein (Mietauto!)\n"),
        ("Strand Praia da Marinha.jpg", "photo", "beach"),
        ("Altstadt Lagos.jpg", "photo", "town"),
        ("Sonnenuntergang.jpg", "photo", "sunset"),
        ("Abendessen am Hafen.jpg", "photo", "dinner"),
        ("Bootsfahrt zu den Grotten.mp4", "video", "boat"),
        ("Rechnung Restaurant O Marinheiro.pdf", "pdf",
         ("Restaurante O Marinheiro, Lagos", "Rechnung Nr. 4471",
          ["8. August 2026, Tisch 12"],
          [("Gegrillte Sardinen, 2×", "29,00"), ("Cataplana, 1×", "38,00"), ("Vinho Verde, 1 Flasche", "18,50"),
           ("Pastéis de nata, 2×", "5,00")])),
        ("Tankbeleg.pdf", "pdf",
         ("Galp Lagos", "Beleg Nr. 30917", ["13. August 2026, Zapfsäule 4"],
          [("Super 95, 38,2 Liter", "71,80")])),
        ("Kostenaufstellung.md", "note",
         "# Kostenaufstellung Algarve 2026\n\n"
         "| Was | Betrag (€) |\n| --- | ---: |\n"
         "| Flug und Hotel (Reisebüro) | 2.159,00 |\n| Mietauto | 351,00 |\n| Versicherung | 89,00 |\n"
         "| Essen und Trinken | 640,00 |\n| Tanken | 71,80 |\n| Ausflüge | 120,00 |\n"
         "| **Summe** | **3.430,80** |\n\nAnna zahlt die Hälfte: **1.715,40 €**\n"),
    ],
    "en": [
        ("Trip ideas.md", "note",
         "# Trip ideas summer 2026\n\n"
         "- **Portugal, Algarve** – beaches, cliffs, great food. Anna has been there.\n"
         "- Croatia, Istria – close, but very crowded in August.\n"
         "- Sardinia – beautiful, but the ferry is expensive.\n\n"
         "Decision: **Algarve, August 1–14.** Fly to Faro, rent a car.\n"),
        ("Offer travel agency Sunshine.pdf", "pdf",
         ("Sunshine Travel", "Offer no. 2026-0412",
          ["Algarve, August 1 to 14, 2026, 2 people", "Flight Vienna–Faro, Hotel Casa Azul in Lagos"],
          [("Flight Vienna–Faro and back, 2 people", "684.00"), ("Hotel Casa Azul, 13 nights", "1,430.00"),
           ("Service fee", "45.00")])),
        ("Flight booking Vienna–Faro.pdf", "pdf",
         ("SkyLine Airways", "Booking confirmation LX7KQ2",
          ["Outbound: Sat Aug 1, 2026, Vienna 07:15 – Faro 10:05",
           "Return: Fri Aug 14, 2026, Faro 18:40 – Vienna 23:20", "Passengers: 2 adults, 1 suitcase each"], None)),
        ("Hotel confirmation Casa Azul.pdf", "pdf",
         ("Casa Azul, Lagos", "Reservation confirmation",
          ["Arrival Aug 1, 2026, departure Aug 14, 2026", "Double room with sea view, breakfast included",
           "Free cancellation until Jul 1, 2026"], None)),
        ("Rental car booking.pdf", "pdf",
         ("RentaCar Faro", "Rental agreement no. 88231",
          ["Pick-up Faro airport, Aug 1, 2026, 10:30", "Compact car, full coverage without deductible"],
          [("Rental 13 days", "312.00"), ("Additional driver", "39.00")])),
        ("Travel insurance policy.pdf", "pdf",
         ("Worldwide Insurance Ltd.", "Policy RV-551203",
          ["Travel cover for 2 people, Aug 1 to Aug 14, 2026",
           "Cancellation, health, luggage – deductible 0 €"], [("Premium", "89.00")])),
        ("Mail from Anna – I'm coming along.eml", "mail",
         ("Anna Berger <anna.berger@example.org>", "you@example.org", "I'm coming along!",
          "Mon, 02 Mar 2026 19:42:00 +0100",
          "Hi!\n\nI talked to my boss: I get the two weeks off.\n"
          "So I'm coming along to the Algarve! Send me the flight details and I'll book too.\n\n"
          "See you soon,\nAnna\n")),
        ("Packing list.md", "note",
         "# Packing list\n\n- [ ] Passport\n- [ ] Swimwear\n- [ ] Sunscreen\n- [ ] Chargers\n"
         "- [ ] Hiking shoes for the cliffs\n- [ ] Driving licence (rental car!)\n"),
        ("Beach Praia da Marinha.jpg", "photo", "beach"),
        ("Old town Lagos.jpg", "photo", "town"),
        ("Sunset.jpg", "photo", "sunset"),
        ("Dinner at the harbour.jpg", "photo", "dinner"),
        ("Boat trip to the grottoes.mp4", "video", "boat"),
        ("Invoice restaurant O Marinheiro.pdf", "pdf",
         ("Restaurante O Marinheiro, Lagos", "Invoice no. 4471",
          ["August 8, 2026, table 12"],
          [("Grilled sardines, 2×", "29.00"), ("Cataplana, 1×", "38.00"), ("Vinho Verde, 1 bottle", "18.50"),
           ("Pastéis de nata, 2×", "5.00")])),
        ("Fuel receipt.pdf", "pdf",
         ("Galp Lagos", "Receipt no. 30917", ["August 13, 2026, pump 4"],
          [("Unleaded 95, 38.2 litres", "71.80")])),
        ("Cost overview.md", "note",
         "# Cost overview Algarve 2026\n\n"
         "| What | Amount (€) |\n| --- | ---: |\n"
         "| Flight and hotel (travel agency) | 2,159.00 |\n| Rental car | 351.00 |\n| Insurance | 89.00 |\n"
         "| Food and drinks | 640.00 |\n| Fuel | 71.80 |\n| Excursions | 120.00 |\n"
         "| **Total** | **3,430.80** |\n\nAnna pays half: **1,715.40 €**\n"),
    ],
}

MOROCCO = {
    "de": [
        ("Reiseplan Marokko.md", "note",
         "# Reiseplan Marokko, Oktober 2025\n\n"
         "1. Marrakesch – 3 Nächte im Riad Dar Yasmine\n2. Über den Atlas ins Draa-Tal\n"
         "3. Zwei Nächte in der Wüste, Erg Chebbi\n4. Zurück über Ouarzazate\n\n"
         "Reiseführer: Karim, Kontakt über das Riad.\n"),
        ("Flugtickets Wien–Marrakesch.pdf", "pdf",
         ("SkyLine Airways", "E-Ticket QF29PL",
          ["Hinflug: 10.10.2025, Wien 09:40 – Marrakesch 13:05", "Rückflug: 20.10.2025, Marrakesch 14:30 – Wien 19:50"],
          [("2 Tickets inkl. Gepäck", "498,00")])),
        ("Riad Dar Yasmine Bestätigung.pdf", "pdf",
         ("Riad Dar Yasmine, Marrakesch", "Buchungsbestätigung",
          ["10. bis 13. Oktober 2025, Zimmer Safran, Frühstück auf der Dachterrasse"],
          [("3 Nächte", "345,00")])),
        ("Wüstentour Angebot.pdf", "pdf",
         ("Sahara Trails", "Angebot Wüstentour",
          ["4 Tage Marrakesch – Erg Chebbi – Marrakesch", "Fahrer, Zeltcamp, Kamelritt bei Sonnenuntergang"],
          [("Tour für 2 Personen", "620,00")])),
        ("Mail von Karim – Abholung.eml", "mail",
         ("Karim El Amrani <karim@example.org>", "du@example.org", "Abholung am 13. Oktober",
          "Wed, 08 Oct 2025 11:15:00 +0100",
          "Salam!\n\nIch hole euch am 13. Oktober um 8 Uhr am Riad ab.\n"
          "Bitte warme Jacken mitnehmen – in der Wüste wird es nachts kalt.\n\nKarim\n")),
        ("Djemaa el Fna.jpg", "photo", "market"),
        ("Atlasgebirge.jpg", "photo", "mountains"),
        ("Dünen Erg Chebbi.jpg", "photo", "desert"),
        ("Kamelritt.mp4", "video", "camels"),
        ("Rechnung Teppich.pdf", "pdf",
         ("Bazar Atlas, Marrakesch", "Rechnung Nr. 118",
          ["Berberteppich, 120 × 180 cm, Versand nach Wien"], [("Teppich", "280,00"), ("Versand", "60,00")])),
        ("Kostenaufstellung.md", "note",
         "# Kosten Marokko 2025\n\n| Was | Betrag (€) |\n| --- | ---: |\n| Flüge | 498,00 |\n"
         "| Riad | 345,00 |\n| Wüstentour | 620,00 |\n| Teppich mit Versand | 340,00 |\n"
         "| Essen und Sonstiges | 410,00 |\n| **Summe** | **2.213,00** |\n"),
    ],
    "en": [
        ("Travel plan Morocco.md", "note",
         "# Travel plan Morocco, October 2025\n\n"
         "1. Marrakesh – 3 nights at Riad Dar Yasmine\n2. Across the Atlas into the Draa valley\n"
         "3. Two nights in the desert, Erg Chebbi\n4. Back via Ouarzazate\n\n"
         "Guide: Karim, contact through the riad.\n"),
        ("Flight tickets Vienna–Marrakesh.pdf", "pdf",
         ("SkyLine Airways", "E-ticket QF29PL",
          ["Outbound: Oct 10, 2025, Vienna 09:40 – Marrakesh 13:05",
           "Return: Oct 20, 2025, Marrakesh 14:30 – Vienna 19:50"],
          [("2 tickets incl. luggage", "498.00")])),
        ("Riad Dar Yasmine confirmation.pdf", "pdf",
         ("Riad Dar Yasmine, Marrakesh", "Booking confirmation",
          ["October 10 to 13, 2025, room Saffron, breakfast on the roof terrace"],
          [("3 nights", "345.00")])),
        ("Desert tour offer.pdf", "pdf",
         ("Sahara Trails", "Desert tour offer",
          ["4 days Marrakesh – Erg Chebbi – Marrakesh", "Driver, tent camp, camel ride at sunset"],
          [("Tour for 2 people", "620.00")])),
        ("Mail from Karim – pick-up.eml", "mail",
         ("Karim El Amrani <karim@example.org>", "you@example.org", "Pick-up on October 13",
          "Wed, 08 Oct 2025 11:15:00 +0100",
          "Salam!\n\nI'll pick you up at the riad on October 13 at 8 am.\n"
          "Please bring warm jackets – the desert gets cold at night.\n\nKarim\n")),
        ("Jemaa el-Fnaa.jpg", "photo", "market"),
        ("Atlas mountains.jpg", "photo", "mountains"),
        ("Dunes Erg Chebbi.jpg", "photo", "desert"),
        ("Camel ride.mp4", "video", "camels"),
        ("Invoice carpet.pdf", "pdf",
         ("Bazar Atlas, Marrakesh", "Invoice no. 118",
          ["Berber carpet, 120 × 180 cm, shipping to Vienna"], [("Carpet", "280.00"), ("Shipping", "60.00")])),
        ("Cost overview.md", "note",
         "# Costs Morocco 2025\n\n| What | Amount (€) |\n| --- | ---: |\n| Flights | 498.00 |\n"
         "| Riad | 345.00 |\n| Desert tour | 620.00 |\n| Carpet incl. shipping | 340.00 |\n"
         "| Food and other | 410.00 |\n| **Total** | **2,213.00** |\n"),
    ],
}

# Lesson 10: two small projects, each with tags of its own (.MyOS/Tags.md); tags in notes are
# words with # in front (several words with a hyphen). Lesson 11: a company whose rights are
# in .MyOS/ACLs.md. Paths below are relative to the lesson's folder.

def _project(name, colour):
    return (f"{name}/.MyOS/Project.md", "note", f"color: {colour}\n")


def _tags(name, tags):
    return (f"{name}/.MyOS/Tags.md", "note", "# Tags\n" + "".join(f"#{tag}\n" for tag in tags))


TAGS = {
    "de": [
        ("Übungen zu Tags.md", "note",
         "# Übungen zu Tags\n\n"
         "In dieser Lektion liegen zwei kleine Projekte: **Wohnungsrenovierung** und **Haushaltsfinanzen**. "
         "Jedes bringt seine eigenen Tags mit.\n\n"
         "## 1. Tags finden und filtern\n"
         "Öffne die *Wohnungsrenovierung* in Scope. Rechts unter **Filetags** siehst du die Tags der Notizen: "
         "#wichtig, #dringend, #in-Arbeit, #erledigt. Klick auf #dringend: Jetzt siehst du nur noch, was dringend ist. "
         "Ein zweiter Klick zeigt wieder alles.\n\n"
         "## 2. Selbst taggen\n"
         "Öffne die Notiz „Ideen für den Balkon\" und schreib irgendwo #wichtig hinein. Zurück in Scope: "
         "Sie erscheint jetzt unter #wichtig. So einfach ist ein Tag in einer Notiz – ein Wort mit # davor. "
         "Tags aus mehreren Wörtern schreibst du mit Bindestrich: #in-Arbeit.\n\n"
         "## 3. Einen Ordner taggen\n"
         "Öffne den Ordner *Bad*. Rechts unter **Dieser Ordner** steht ein blasser Tag ohne Namen. Klick darauf "
         "und gib dem Ordner einen Tag. Schau, was dir vorgeschlagen wird: genau die Tags dieses Projekts. "
         "Wähle #in-Arbeit. Mit einem Rechtsklick auf den Tag gibst du ihm eine Farbe.\n\n"
         "## 4. Anderes Projekt, andere Tags\n"
         "Öffne jetzt die *Haushaltsfinanzen* und gib dem Ordner *Belege 2026* einen Tag. Die Vorschläge sind "
         "ganz andere: #bezahlt, #nicht-bezahlt, #wartend ... So halten Projekte die Flut an Tags im Zaum. "
         "Filtere dann nach #nicht-bezahlt: Was musst du noch bezahlen?\n\n"
         "## 5. Wo die Tags eines Projekts stehen\n"
         "Die Tags eines Projekts stehen in einer Notiz: *.MyOS/Tags.md* im Projektordner. *.MyOS* ist ein "
         "versteckter Ordner – in Scope zeigst du ihn mit ⚙ → Scope → Versteckte Ordner. Ergänze dort eine "
         "Zeile #Steuer: Ab jetzt wird sie dir in diesem Projekt vorgeschlagen.\n\n"
         "---\n"
         "Noch nicht möglich: beliebige Dateien wie PDFs oder Fotos zu taggen, und Tags mit einer Zahl "
         "(zu 40 % erledigt). Daran arbeiten wir.\n\n"
         "[Zurück zur Lektion](<Tags.md>)\n"),
        _project("Wohnungsrenovierung", "#c07a2c"),
        _tags("Wohnungsrenovierung", ["wichtig", "dringend", "in-Arbeit", "erledigt"]),
        ("Wohnungsrenovierung/Elektriker anrufen.md", "note",
         "# Elektriker anrufen\n\nIm Bad funktioniert die Steckdose neben dem Spiegel nicht. "
         "Bevor gefliest wird, muss der Elektriker kommen!\n\n#wichtig #dringend\n"),
        ("Wohnungsrenovierung/Fliesen aussuchen.md", "note",
         "# Fliesen aussuchen\n\nMuster im Baumarkt angeschaut: Grau 30 × 60 oder Weiß mit Struktur.\n\n#in-Arbeit\n"),
        ("Wohnungsrenovierung/Wohnzimmer ausmalen.md", "note",
         "# Wohnzimmer ausmalen\n\nAm Wochenende erledigt, zwei Anstriche.\n\n#erledigt\n"),
        ("Wohnungsrenovierung/Küche planen.md", "note",
         "# Küche planen\n\nWo soll der Herd hin? Termin im Küchenstudio ausmachen.\n\n#wichtig\n"),
        ("Wohnungsrenovierung/Ideen für den Balkon.md", "note",
         "# Ideen für den Balkon\n\n- Hochbeet für Kräuter\n- Lichterkette\n- Zwei Klappstühle\n"),
        ("Wohnungsrenovierung/Bad/Maße Bad.md", "note",
         "# Maße Bad\n\nBreite 2,10 m, Tiefe 1,80 m, Höhe 2,50 m. Fenster 80 × 60 cm.\n"),
        ("Wohnungsrenovierung/Küche/Angebot Küchenstudio.md", "note",
         "# Angebot Küchenstudio\n\nZeile mit 2,80 m, Geräte inklusive: 6.900 €. Gültig bis Ende Mai.\n\n#in-Arbeit\n"),
        _project("Haushaltsfinanzen", "#3c8d5a"),
        _tags("Haushaltsfinanzen", ["nicht-bezahlt", "verschoben", "wartend", "eingetrieben", "bezahlt"]),
        ("Haushaltsfinanzen/Stromrechnung März.md", "note",
         "# Stromrechnung März\n\n64,20 €, abgebucht am 5. April.\n\n#bezahlt\n"),
        ("Haushaltsfinanzen/Internet April.md", "note",
         "# Internet April\n\n39,90 €, fällig am 20. April.\n\n#nicht-bezahlt\n"),
        ("Haushaltsfinanzen/Kündigung Fitnessstudio.md", "note",
         "# Kündigung Fitnessstudio\n\nKündigung geschickt, die Bestätigung fehlt noch.\n\n#wartend\n"),
        ("Haushaltsfinanzen/Geld von Paul.md", "note",
         "# Geld von Paul\n\nPaul hat die 50 € für das Konzertticket zurückgezahlt.\n\n#eingetrieben\n"),
        ("Haushaltsfinanzen/Autoversicherung.md", "note",
         "# Autoversicherung\n\nJahresprämie 480 €. Ratenzahlung bis Juni aufgeschoben.\n\n#verschoben\n"),
        ("Haushaltsfinanzen/Zahnarztrechnung.md", "note",
         "# Zahnarztrechnung\n\n120 € für die Mundhygiene. Noch nicht überwiesen.\n"),
        ("Haushaltsfinanzen/Belege 2026/Was hier hinkommt.md", "note",
         "# Belege 2026\n\nAlle Kassenzettel und Belege dieses Jahres.\n"),
    ],
    "en": [
        ("Tag exercises.md", "note",
         "# Tag exercises\n\n"
         "In this lesson there are two small projects: **Apartment renovation** and **Household finances**. "
         "Each brings its own tags.\n\n"
         "## 1. Find tags and filter\n"
         "Open *Apartment renovation* in Scope. On the right, under **File tags**, you see the tags of the notes: "
         "#important, #urgent, #in-progress, #done. Click #urgent: now you only see what is urgent. "
         "A second click shows everything again.\n\n"
         "## 2. Tag something yourself\n"
         "Open the note \"Balcony ideas\" and write #important somewhere in it. Back in Scope: it now shows up "
         "under #important. That's how easy a tag in a note is – a word with # in front. "
         "Write tags of several words with a hyphen: #in-progress.\n\n"
         "## 3. Tag a folder\n"
         "Open the folder *Bathroom*. On the right, under **This folder**, there is a pale tag without a name. "
         "Click it and give the folder a tag. Look at what is suggested: exactly the tags of this project. "
         "Choose #in-progress. Right-click the tag to give it a colour.\n\n"
         "## 4. Another project, other tags\n"
         "Now open *Household finances* and give the folder *Receipts 2026* a tag. The suggestions are quite "
         "different: #paid, #not-paid, #waiting ... That's how projects keep the flood of tags in check. "
         "Then filter by #not-paid: what do you still have to pay?\n\n"
         "## 5. Where a project's tags are\n"
         "A project's tags are in a note: *.MyOS/Tags.md* in the project folder. *.MyOS* is a hidden folder – "
         "in Scope you show it with ⚙ → Scope → Hidden folders. Add a line #tax there: from now on it is "
         "suggested in this project.\n\n"
         "---\n"
         "Not possible yet: tagging any file, like PDFs or photos, and tags with a number (40 % done). "
         "We are working on it.\n\n"
         "[Back to the lesson](<Tags.md>)\n"),
        _project("Apartment renovation", "#c07a2c"),
        _tags("Apartment renovation", ["important", "urgent", "in-progress", "done"]),
        ("Apartment renovation/Call the electrician.md", "note",
         "# Call the electrician\n\nThe socket next to the bathroom mirror doesn't work. "
         "The electrician has to come before the tiling!\n\n#important #urgent\n"),
        ("Apartment renovation/Choose tiles.md", "note",
         "# Choose tiles\n\nLooked at samples in the DIY store: grey 30 × 60 or white with texture.\n\n#in-progress\n"),
        ("Apartment renovation/Paint the living room.md", "note",
         "# Paint the living room\n\nDone at the weekend, two coats.\n\n#done\n"),
        ("Apartment renovation/Plan the kitchen.md", "note",
         "# Plan the kitchen\n\nWhere should the stove go? Make an appointment at the kitchen studio.\n\n#important\n"),
        ("Apartment renovation/Balcony ideas.md", "note",
         "# Balcony ideas\n\n- Raised bed for herbs\n- Fairy lights\n- Two folding chairs\n"),
        ("Apartment renovation/Bathroom/Bathroom measurements.md", "note",
         "# Bathroom measurements\n\nWidth 2.10 m, depth 1.80 m, height 2.50 m. Window 80 × 60 cm.\n"),
        ("Apartment renovation/Kitchen/Kitchen studio offer.md", "note",
         "# Kitchen studio offer\n\nOne row of 2.80 m, appliances included: 6,900 €. Valid until the end of May.\n\n"
         "#in-progress\n"),
        _project("Household finances", "#3c8d5a"),
        _tags("Household finances", ["not-paid", "postponed", "waiting", "collected", "paid"]),
        ("Household finances/Electricity bill March.md", "note",
         "# Electricity bill March\n\n64.20 €, debited on April 5.\n\n#paid\n"),
        ("Household finances/Internet April.md", "note",
         "# Internet April\n\n39.90 €, due on April 20.\n\n#not-paid\n"),
        ("Household finances/Gym cancellation.md", "note",
         "# Gym cancellation\n\nCancellation sent, the confirmation is still missing.\n\n#waiting\n"),
        ("Household finances/Money from Paul.md", "note",
         "# Money from Paul\n\nPaul paid back the 50 € for the concert ticket.\n\n#collected\n"),
        ("Household finances/Car insurance.md", "note",
         "# Car insurance\n\nAnnual premium 480 €. Instalments postponed until June.\n\n#postponed\n"),
        ("Household finances/Dentist bill.md", "note",
         "# Dentist bill\n\n120 € for the dental hygiene. Not transferred yet.\n"),
        ("Household finances/Receipts 2026/What goes here.md", "note",
         "# Receipts 2026\n\nAll receipts and slips of this year.\n"),
    ],
}

ACLS = {
    "de": ("# Permissions\n\n"
           "## Admin\n- /*: read, write, execute, delete\n- /.MyOS/ACLs.md: read, write, change\n\n"
           "## Geschäftsleitung\n- /*: read\n- /07_Arbeit/Vertraulich/: read, write\n\n"
           "## Buchhaltung\n- /01_Info/: read\n- /04_Finanz/: read, write\n- /05_Rechtliches/: read\n\n"
           "## Team\n- /01_Info/: read\n- /07_Arbeit/: read, write\n- /07_Arbeit/Vertraulich/: none\n"
           "- /08_Dokumentation/: read\n\n"
           "## Gast\n- /01_Info/: read\n\n"
           "# Users\nEva Muster: Geschäftsleitung\nAnna Huber: Buchhaltung\nKarl Berger: Team\nMia Novak: Gast\n"),
    "en": ("# Permissions\n\n"
           "## Admin\n- /*: read, write, execute, delete\n- /.MyOS/ACLs.md: read, write, change\n\n"
           "## Management\n- /*: read\n- /07_Work/Confidential/: read, write\n\n"
           "## Accounting\n- /01_Info/: read\n- /04_Finance/: read, write\n- /05_Legal/: read\n\n"
           "## Team\n- /01_Info/: read\n- /07_Work/: read, write\n- /07_Work/Confidential/: none\n"
           "- /08_Documentation/: read\n\n"
           "## Guest\n- /01_Info/: read\n\n"
           "# Users\nEva Muster: Management\nAnna Huber: Accounting\nKarl Berger: Team\nMia Novak: Guest\n"),
}

COMPANY = {
    "de": [
        ("Übungen zu Zugriffsrechten.md", "note",
         "# Übungen zu Zugriffsrechten\n\n"
         "In dieser Lektion liegt die **Musterfirma** mit vier Menschen: Eva Muster (Geschäftsleitung), "
         "Anna Huber (Buchhaltung), Karl Berger (Team) und Mia Novak (Gast). Wer was darf, steht in einer "
         "einzigen Notiz: *.MyOS/ACLs.md*.\n\n"
         "## 1. Wer darf hier hinein?\n"
         "Öffne die Musterfirma in Scope. Links unter **Zugriff** siehst du, wer auf den angezeigten Ordner "
         "zugreifen darf – Gruppen und Menschen, mit kleinen Pfeilen: ◂ lesen, ▸ schreiben. Geh in *04_Finanz*: "
         "Jetzt steht dort die Buchhaltung. Geh in *07_Arbeit/Vertraulich*: Hier darf das Team nicht hinein, "
         "nur die Geschäftsleitung.\n"
         "Scope sagt dir vielleicht: „Du bist in diesem Projekt nicht eingetragen. Wer bist du?\" – das lässt "
         "du für den Moment; in Übung 4 trägst du dich selbst ein.\n\n"
         "## 2. Mit den Augen einer Gruppe\n"
         "Klick links auf *Team*: Scope zeigt nur noch, worauf das Team zugreifen darf. Ein zweiter Klick "
         "zeigt wieder alles.\n\n"
         "## 3. Eine einzige Zeile\n"
         "Öffne *.MyOS/ACLs.md*. *.MyOS* ist ein versteckter Ordner – in Scope zeigst du ihn mit ⚙ → Scope → "
         "Versteckte Ordner. Unter **## Gast** steht `- /01_Info/: read`. Diese eine Zeile sagt: Gäste dürfen "
         "/01_Info/ lesen – und sonst nichts.\n\n"
         "## 4. Selbst Admin werden (für Fortgeschrittene)\n"
         "Rechte ändern darf nur, wer Admin ist – und in der Musterfirma ist das noch niemand. Schreib in der "
         "ACLs.md unter **# Users** eine neue Zeile: deinen Benutzernamen auf diesem Computer (so heißt dein "
         "persönlicher Ordner unter /home), einen Doppelpunkt und *Admin*, zum Beispiel `maria: Admin`.\n"
         "Zurück in Scope änderst du jetzt mit einem **Rechtsklick** auf eine Gruppe ihre Rechte für den "
         "angezeigten Ordner. Gib zum Beispiel dem Team in *04_Finanz* Leserechte. Schau danach in die "
         "ACLs.md: Genau eine Zeile ist dazugekommen. Die vorige Fassung bewahrt MyOS in "
         "*.MyOS/ACLs-history* auf.\n\n"
         "## 5. Eine neue Kollegin\n"
         "Links unten findest du jetzt **+ Person**. Füge Lea Wagner hinzu und gib ihr die Gruppe Team. "
         "Auch das steht danach als eine Zeile in der ACLs.md.\n\n"
         "---\n"
         "Gut zu wissen: Ob MyOS die Rechte auch durchsetzt, ist derzeit noch ein Schalter für Entwickler. "
         "In diesen Übungen siehst du, wer was darf – verstecken wird MyOS dabei noch nichts.\n\n"
         "[Zurück zur Lektion](<Zugriffsrechte.md>)\n"),
        _project("Musterfirma", "#4c72d9"),
        ("Musterfirma/.MyOS/ACLs.md", "note", ACLS["de"]),
        ("Musterfirma/00_Admin/Firmenbuchauszug.pdf", "pdf",
         ("Firmenbuch", "Auszug FN 512344 k", ["Musterfirma GmbH, Hauptstraße 1, 1010 Wien",
                                                 "Geschäftsführerin: Eva Muster"], None)),
        ("Musterfirma/01_Info/Willkommen im Team.md", "note",
         "# Willkommen im Team!\n\nSchön, dass du da bist. Hier findest du alles für deine ersten Tage: "
         "Schlüssel bei Anna, WLAN-Passwort am Empfang, Mittagessen meistens um 12.\n"),
        ("Musterfirma/02_Team/Mitarbeiter/Anna Huber.md", "note",
         "# Anna Huber\n\nBuchhaltung, seit 2019. Durchwahl 12.\n"),
        ("Musterfirma/02_Team/Mitarbeiter/Karl Berger.md", "note",
         "# Karl Berger\n\nEntwicklung, seit 2022. Durchwahl 15.\n"),
        ("Musterfirma/04_Finanz/Ausgaben/Rechnung Büromaterial.pdf", "pdf",
         ("Papier & Co", "Rechnung Nr. 7781", ["Lieferung an Musterfirma GmbH, 3. März 2026"],
          [("Druckerpapier, 10 Packungen", "54,90"), ("Ordner, 20 Stück", "39,80"), ("Kugelschreiber, 50 Stück", "24,50")])),
        ("Musterfirma/04_Finanz/Einnahmen/Rechnung an Bäckerei Sonne.pdf", "pdf",
         ("Musterfirma GmbH", "Rechnung Nr. 2026-031", ["An: Bäckerei Sonne, Neubaugasse 7, 1070 Wien"],
          [("Neue Website, Pauschale", "2.400,00"), ("Hosting 2026", "180,00")])),
        ("Musterfirma/05_Rechtliches/Mietvertrag Büro.md", "note",
         "# Mietvertrag Büro\n\nHauptstraße 1, 2. Stock, 140 m². Miete 2.300 € im Monat, "
         "Kündigungsfrist drei Monate.\n"),
        ("Musterfirma/07_Arbeit/Projektplan Website Bäckerei Sonne.md", "note",
         "# Projektplan Website Bäckerei Sonne\n\n1. Entwurf bis 15. März\n2. Texte und Fotos bis 31. März\n"
         "3. Online am 15. April\n"),
        ("Musterfirma/07_Arbeit/Vertraulich/Gehälter 2026.md", "note",
         "# Gehälter 2026\n\nNur für die Geschäftsleitung.\n\n| Name | Monat (€) |\n| --- | ---: |\n"
         "| Anna Huber | 3.400 |\n| Karl Berger | 3.900 |\n"),
        ("Musterfirma/08_Dokumentation/Firmenfeier.jpg", "photo", "dinner"),
    ],
    "en": [
        ("Access rights exercises.md", "note",
         "# Access rights exercises\n\n"
         "In this lesson there is the **Sample Company** with four people: Eva Muster (management), "
         "Anna Huber (accounting), Karl Berger (team) and Mia Novak (guest). Who may do what is in one "
         "single note: *.MyOS/ACLs.md*.\n\n"
         "## 1. Who may enter here?\n"
         "Open the Sample Company in Scope. On the left, under **Access**, you see who may access the folder "
         "shown – groups and people, with small arrows: ◂ read, ▸ write. Go into *04_Finance*: now accounting "
         "is listed there. Go into *07_Work/Confidential*: the team may not enter here, only the management.\n"
         "Scope may tell you: \"You are not listed in this project. Who are you?\" – leave that for now; in "
         "exercise 4 you add yourself.\n\n"
         "## 2. Through the eyes of a group\n"
         "Click *Team* on the left: Scope only shows what the team may access. A second click shows "
         "everything again.\n\n"
         "## 3. One single line\n"
         "Open *.MyOS/ACLs.md*. *.MyOS* is a hidden folder – in Scope you show it with ⚙ → Scope → Hidden "
         "folders. Under **## Guest** it says `- /01_Info/: read`. This one line says: guests may read "
         "/01_Info/ – and nothing else.\n\n"
         "## 4. Become admin yourself (advanced)\n"
         "Only an admin may change rights – and in the Sample Company nobody is one yet. In ACLs.md, under "
         "**# Users**, write a new line: your user name on this computer (the name of your personal folder "
         "under /home), a colon, and *Admin*, for example `maria: Admin`.\n"
         "Back in Scope, you can now **right-click** a group to change its rights for the folder shown. "
         "For example, give the team read access in *04_Finance*. Then look into ACLs.md: exactly one line "
         "has been added. MyOS keeps the previous version in *.MyOS/ACLs-history*.\n\n"
         "## 5. A new colleague\n"
         "At the bottom left you now find **+ Person**. Add Lea Wagner and give her the group Team. "
         "That, too, is one line in ACLs.md afterwards.\n\n"
         "---\n"
         "Good to know: whether MyOS also enforces the rights is still a switch for developers. In these "
         "exercises you see who may do what – MyOS won't hide anything yet.\n\n"
         "[Back to the lesson](<Access Rights.md>)\n"),
        _project("Sample Company", "#4c72d9"),
        ("Sample Company/.MyOS/ACLs.md", "note", ACLS["en"]),
        ("Sample Company/00_Admin/Company register extract.pdf", "pdf",
         ("Company Register", "Extract FN 512344 k", ["Sample Company Ltd., Main Street 1, Vienna",
                                                       "Managing director: Eva Muster"], None)),
        ("Sample Company/01_Info/Welcome to the team.md", "note",
         "# Welcome to the team!\n\nGood to have you here. Everything for your first days: keys from Anna, "
         "Wi-Fi password at the reception, lunch mostly at noon.\n"),
        ("Sample Company/02_Team/Staff/Anna Huber.md", "note",
         "# Anna Huber\n\nAccounting, since 2019. Extension 12.\n"),
        ("Sample Company/02_Team/Staff/Karl Berger.md", "note",
         "# Karl Berger\n\nDevelopment, since 2022. Extension 15.\n"),
        ("Sample Company/04_Finance/Expenses/Invoice office supplies.pdf", "pdf",
         ("Paper & Co", "Invoice no. 7781", ["Delivery to Sample Company Ltd., March 3, 2026"],
          [("Printer paper, 10 packs", "54.90"), ("Binders, 20 pieces", "39.80"), ("Pens, 50 pieces", "24.50")])),
        ("Sample Company/04_Finance/Income/Invoice to Sunshine Bakery.pdf", "pdf",
         ("Sample Company Ltd.", "Invoice no. 2026-031", ["To: Sunshine Bakery, New Street 7, Vienna"],
          [("New website, flat rate", "2,400.00"), ("Hosting 2026", "180.00")])),
        ("Sample Company/05_Legal/Office lease.md", "note",
         "# Office lease\n\nMain Street 1, 2nd floor, 140 m². Rent 2,300 € per month, three months' notice.\n"),
        ("Sample Company/07_Work/Project plan Sunshine Bakery website.md", "note",
         "# Project plan Sunshine Bakery website\n\n1. Design by March 15\n2. Texts and photos by March 31\n"
         "3. Online on April 15\n"),
        ("Sample Company/07_Work/Confidential/Salaries 2026.md", "note",
         "# Salaries 2026\n\nManagement only.\n\n| Name | Month (€) |\n| --- | ---: |\n"
         "| Anna Huber | 3,400 |\n| Karl Berger | 3,900 |\n"),
        ("Sample Company/08_Documentation/Company party.jpg", "photo", "dinner"),
    ],
}

# Where they go: lesson folder of each language, and the folder names the lessons mention.
LESSONS = {
    "de": {"loose": "DE/Lektion04", "unsorted": "DE/Lektion05/Urlaub Sommer 2026",
           "other": "DE/Lektion07/Urlaub 2025", "tags": "DE/Lektion10", "rights": "DE/Lektion11", "total": "Summe"},
    "en": {"loose": "EN/Lesson04", "unsorted": "EN/Lesson05/vacation summer 2026",
           "other": "EN/Lesson07/vacation 2025", "tags": "EN/Lesson10", "rights": "EN/Lesson11", "total": "Total"},
}


# --- Drawing --------------------------------------------------------------------------------

def _gradient(draw, box, top, bottom):
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        draw.line([(x0, y), (x1, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))


def draw_scene(scene, width=800, height=533, phase=0.0):
    """A small painted landscape (no text: they are photos). phase moves what moves in a video."""
    rng = random.Random(scene)  # the same scene is always the same picture
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    horizon = int(height * 0.55)
    if scene in ("beach", "boat"):
        _gradient(draw, (0, 0, width, horizon), (90, 160, 230), (190, 225, 250))
        _gradient(draw, (0, horizon, width, height), (20, 110, 170), (40, 150, 190))
        draw.ellipse((width * 0.78, height * 0.08, width * 0.9, height * 0.26), fill=(255, 240, 170))
        if scene == "beach":
            draw.polygon([(0, height), (0, height * 0.72), (width * 0.55, height * 0.86), (width, height * 0.8),
                          (width, height)], fill=(232, 205, 150))
            draw.polygon([(0, horizon), (width * 0.12, height * 0.2), (width * 0.3, height * 0.32), (width * 0.36, horizon)],
                         fill=(200, 120, 70))
        else:
            x = width * (0.1 + 0.7 * phase)
            draw.polygon([(x, horizon + 60), (x + 120, horizon + 60), (x + 100, horizon + 90), (x + 15, horizon + 90)],
                         fill=(240, 240, 235))
            draw.line([(x + 60, horizon + 60), (x + 60, horizon - 20)], fill=(90, 70, 50), width=4)
            draw.polygon([(x + 62, horizon - 18), (x + 62, horizon + 55), (x + 110, horizon + 55)], fill=(250, 250, 250))
            draw.polygon([(width * 0.6, horizon), (width * 0.75, height * 0.3), (width, height * 0.25), (width, horizon)],
                         fill=(195, 125, 75))
    elif scene == "sunset":
        _gradient(draw, (0, 0, width, horizon), (60, 40, 110), (250, 150, 70))
        draw.ellipse((width * 0.42, horizon - 70, width * 0.58, horizon + 70), fill=(255, 200, 90))
        _gradient(draw, (0, horizon, width, height), (120, 70, 90), (40, 30, 60))
    elif scene == "town":
        _gradient(draw, (0, 0, width, height), (110, 175, 235), (200, 230, 250))
        x = 0
        while x < width:
            w = rng.randint(70, 130)
            h = rng.randint(140, 300)
            colour = rng.choice([(245, 240, 230), (240, 210, 170), (230, 180, 150), (250, 250, 245)])
            draw.rectangle((x, height - h, x + w, height), fill=colour)
            draw.polygon([(x - 5, height - h), (x + w / 2, height - h - 35), (x + w + 5, height - h)], fill=(190, 90, 60))
            for wy in range(height - h + 30, height - 40, 55):
                for wx in range(x + 15, x + w - 25, 35):
                    draw.rectangle((wx, wy, wx + 16, wy + 24), fill=(70, 110, 160))
            x += w + 6
    elif scene == "dinner":
        draw.rectangle((0, 0, width, height), fill=(60, 40, 30))
        draw.ellipse((-width * 0.1, height * 0.15, width * 1.1, height * 1.4), fill=(235, 230, 220))
        for cx, cy in ((0.3, 0.55), (0.68, 0.6)):
            draw.ellipse((width * cx - 110, height * cy - 70, width * cx + 110, height * cy + 70), fill=(250, 250, 250),
                         outline=(200, 200, 200), width=3)
            draw.ellipse((width * cx - 60, height * cy - 30, width * cx + 60, height * cy + 30), fill=(200, 130, 60))
        draw.rectangle((width * 0.48, height * 0.2, width * 0.52, height * 0.5), fill=(120, 170, 110))
    elif scene in ("desert", "camels"):
        _gradient(draw, (0, 0, width, horizon), (120, 180, 235), (240, 220, 190))
        for i, colour in enumerate(((235, 170, 100), (220, 145, 80), (205, 125, 65))):
            top = horizon - 40 + i * 70
            points = [(0, height)]
            for x in range(0, width + 40, 40):
                points.append((x, top + 40 * math.sin(x / 120 + i * 1.7)))
            points.append((width, height))
            draw.polygon(points, fill=colour)
        if scene == "camels":
            for k in range(3):
                x = width * (0.05 + 0.6 * phase) + k * 110
                y = horizon + 30
                draw.ellipse((x, y, x + 70, y + 35), fill=(110, 75, 45))
                draw.ellipse((x + 15, y - 18, x + 45, y + 10), fill=(110, 75, 45))
                draw.line([(x + 65, y + 10), (x + 85, y - 25)], fill=(110, 75, 45), width=9)
                draw.ellipse((x + 78, y - 35, x + 98, y - 20), fill=(110, 75, 45))
                for leg in (8, 22, 48, 62):
                    draw.line([(x + leg, y + 30), (x + leg, y + 70)], fill=(110, 75, 45), width=5)
    elif scene == "mountains":
        _gradient(draw, (0, 0, width, height), (130, 185, 235), (225, 235, 245))
        for i, (colour, base) in enumerate((((150, 130, 120), 0.75), ((120, 100, 95), 0.9))):
            x = -100
            while x < width + 100:
                w = rng.randint(220, 360)
                peak = height * rng.uniform(0.15, 0.4) + i * 60
                draw.polygon([(x, height * base + 80), (x + w / 2, peak), (x + w, height * base + 80)], fill=colour)
                draw.polygon([(x + w / 2 - 30, peak + 35), (x + w / 2, peak), (x + w / 2 + 30, peak + 35)],
                             fill=(250, 250, 250))
                x += w - 80
        draw.rectangle((0, height * 0.85, width, height), fill=(170, 140, 90))
    elif scene == "market":
        _gradient(draw, (0, 0, width, height), (240, 170, 110), (130, 80, 60))
        for k in range(6):
            x = k * 140 - 20
            colour = rng.choice([(200, 60, 50), (230, 170, 40), (60, 120, 160), (90, 150, 80)])
            draw.polygon([(x, height * 0.55), (x + 70, height * 0.4), (x + 140, height * 0.55)], fill=colour)
            draw.rectangle((x + 10, height * 0.55, x + 130, height * 0.8), fill=(150, 100, 60))
            for _ in range(12):
                fx = x + rng.randint(15, 120)
                fy = height * 0.58 + rng.randint(0, 50)
                draw.ellipse((fx, fy, fx + 12, fy + 12), fill=rng.choice([(240, 120, 40), (250, 210, 60), (120, 170, 60)]))
        draw.rectangle((width * 0.8, height * 0.1, width * 0.86, height * 0.55), fill=(200, 140, 90))
    else:
        raise ValueError(f"no such scene: {scene}")
    return image


def write_photo(path, scene):
    buffer = io.BytesIO()
    draw_scene(scene).save(buffer, "JPEG", quality=72, optimize=True)
    path.write_bytes(buffer.getvalue())


def write_video(path, scene, seconds=3, fps=10):
    """A few seconds of the scene, the boat or the camels moving; H.264 without metadata."""
    # Drawn at the photos' scale, then made small: the scenes are laid out for that size.
    frames = b"".join(draw_scene(scene, 800, 450, phase=i / (seconds * fps)).resize((320, 180), Image.LANCZOS).tobytes()
                      for i in range(seconds * fps))
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "320x180",
         "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "veryslow", "-crf", "30", "-threads", "1",
         "-pix_fmt", "yuv420p", "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:v", "+bitexact",
         "-movflags", "+faststart", str(path)],
        input=frames, check=True)


def _amount(text, language):
    """'1.430,00' (de) or '1,430.00' (en) as a number."""
    return float(text.replace(".", "").replace(",", ".") if language == "de" else text.replace(",", ""))


def _money(value, language):
    shown = f"{value:,.2f}"
    return shown.replace(",", "_").replace(".", ",").replace("_", ".") if language == "de" else shown


def write_pdf(path, content, language):
    sender, title, lines, items = content
    buffer = io.BytesIO()
    page = canvas.Canvas(buffer, pagesize=A4, invariant=1)  # invariant: no date or id in it
    page.setTitle(title)
    width, height = A4
    page.setFillColorRGB(0.2, 0.3, 0.5)
    page.rect(0, height - 30 * mm, width, 30 * mm, stroke=0, fill=1)
    page.setFillColorRGB(1, 1, 1)
    page.setFont("Helvetica-Bold", 18)
    page.drawString(20 * mm, height - 19 * mm, sender)
    page.setFillColorRGB(0, 0, 0)
    page.setFont("Helvetica-Bold", 15)
    y = height - 50 * mm
    page.drawString(20 * mm, y, title)
    page.setFont("Helvetica", 11)
    for line in lines:
        y -= 8 * mm
        page.drawString(20 * mm, y, line)
    if items:
        y -= 14 * mm
        page.line(20 * mm, y + 5 * mm, width - 20 * mm, y + 5 * mm)
        for what, amount in items:
            page.drawString(20 * mm, y, what)
            page.drawRightString(width - 20 * mm, y, amount + " €")
            y -= 7 * mm
        page.line(20 * mm, y + 5 * mm, width - 20 * mm, y + 5 * mm)
        total = sum(_amount(amount, language) for _, amount in items)
        page.setFont("Helvetica-Bold", 11)
        page.drawString(20 * mm, y - 2 * mm, LESSONS[language]["total"])
        page.drawRightString(width - 20 * mm, y - 2 * mm, _money(total, language) + " €")
    page.showPage()
    page.save()
    path.write_bytes(buffer.getvalue())


def write_mail(path, content):
    sender, to, subject, date, body = content
    path.write_text(
        f"From: {sender}\nTo: {to}\nSubject: {subject}\nDate: {date}\nMIME-Version: 1.0\n"
        f"Content-Type: text/plain; charset=utf-8\nContent-Transfer-Encoding: 8bit\n\n{body}",
        encoding="utf-8")


def write_documents(folder, documents, language):
    folder.mkdir(parents=True, exist_ok=True)
    for name, kind, content in documents:
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)  # names may lie in subfolders
        if kind == "note":
            path.write_text(content, encoding="utf-8")
        elif kind == "pdf":
            write_pdf(path, content, language)
        elif kind == "photo":
            write_photo(path, content)
        elif kind == "video":
            write_video(path, content)
        elif kind == "mail":
            write_mail(path, content)
        else:
            raise ValueError(f"no such kind: {kind}")


def generate(target):
    """Write the exercise files under target (the Learning MyOS folder, or a test's)."""
    target = Path(target)
    for language, places in LESSONS.items():
        loose = target / places["loose"]
        write_documents(loose, ALGARVE[language], language)
        unsorted = target / places["unsorted"]
        unsorted.mkdir(parents=True, exist_ok=True)
        for name, _kind, _content in ALGARVE[language]:  # lesson 5: the same, back in one folder
            shutil.copyfile(loose / name, unsorted / name)
        write_documents(target / places["other"], MOROCCO[language], language)
        write_documents(target / places["tags"], TAGS[language], language)
        write_documents(target / places["rights"], COMPANY[language], language)


if __name__ == "__main__":
    generate(Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "Learning MyOS")
