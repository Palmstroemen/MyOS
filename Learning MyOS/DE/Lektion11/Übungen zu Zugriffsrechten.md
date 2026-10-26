# Übungen zu Zugriffsrechten

In dieser Lektion liegt die **Musterfirma** mit vier Menschen: Eva Muster (Geschäftsleitung), Anna Huber (Buchhaltung), Karl Berger (Team) und Mia Novak (Gast). Wer was darf, steht in einer einzigen Notiz: *.MyOS/ACLs.md*.

## 1. Wer darf hier hinein?
Öffne die Musterfirma in Scope: **[▶ Musterfirma öffnen](<myos:open?scope=Musterfirma>)**. Links unter **Zugriff** siehst du, wer auf den angezeigten Ordner zugreifen darf – Gruppen und Menschen, mit kleinen Pfeilen: ◂ lesen, ▸ schreiben. Geh in *04_Finanz*: Jetzt steht dort die Buchhaltung. Geh in *07_Arbeit/Vertraulich*: Hier darf das Team nicht hinein, nur die Geschäftsleitung.
Scope sagt dir vielleicht: „Du bist in diesem Projekt nicht eingetragen. Wer bist du?" – das lässt du für den Moment; in Übung 4 trägst du dich selbst ein.

## 2. Mit den Augen einer Gruppe
Klick links auf *Team*: Scope zeigt nur noch, worauf das Team zugreifen darf. Ein zweiter Klick zeigt wieder alles.

## 3. Eine einzige Zeile
Öffne *.MyOS/ACLs.md*. *.MyOS* ist ein versteckter Ordner – in Scope zeigst du ihn mit ⚙ → Scope → Versteckte Ordner. Unter **## Gast** steht `- /01_Info/: read`. Diese eine Zeile sagt: Gäste dürfen /01_Info/ lesen – und sonst nichts.

## 4. Selbst Admin werden (für Fortgeschrittene)
Rechte ändern darf nur, wer Admin ist – und in der Musterfirma ist das noch niemand. Schreib in der ACLs.md unter **# Users** eine neue Zeile: deinen Benutzernamen auf diesem Computer (so heißt dein persönlicher Ordner unter /home), einen Doppelpunkt und *Admin*, zum Beispiel `maria: Admin`.
Zurück in Scope änderst du jetzt mit einem **Rechtsklick** auf eine Gruppe ihre Rechte für den angezeigten Ordner. Gib zum Beispiel dem Team in *04_Finanz* Leserechte. Schau danach in die ACLs.md: Genau eine Zeile ist dazugekommen. Die vorige Fassung bewahrt MyOS in *.MyOS/ACLs-history* auf.

## 5. Eine neue Kollegin
Links unten findest du jetzt **+ Person**. Füge Lea Wagner hinzu und gib ihr die Gruppe Team. Auch das steht danach als eine Zeile in der ACLs.md.

---
Gut zu wissen: Ob MyOS die Rechte auch durchsetzt, ist derzeit noch ein Schalter für Entwickler. In diesen Übungen siehst du, wer was darf – verstecken wird MyOS dabei noch nichts.

[Zurück zur Lektion](<Zugriffsrechte.md>)
