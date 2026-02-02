# Begriffe
## CWD
In aktuellen OS gibt es ein current working directory
## CWP
in MyOS gibt es zusätzlich ein current working **project**
Das finden wir, wenn wir vom CWD nach oben suchen, bis wir ein Projekt finden.
## CTD
zusätzlich könnte es etwas geben wie ein current **target** diary.
Das ist, wenn ich im Filebrowser ein File verschieben will und per Click ein File in der Hand habe der Ort an den ich zu navigieren versuche. Dort wo ich letztlich das File droppen will. 
*Ich bin noch nicht sicher, ob es das braucht, und ob wir nicht mit dem CWD durchkommen. Aber als Konzept nehmen wir's einmal.*

# Ein Filebrowser
## Gliederung
Der Filebrowser gliedert sich vertikal in 4 Bereiche (Zeilen).

### Projektbereich
Die oberste Zeile ist der Projektbereich und dieser gliedert sich horizontal in 2 Bereiche (Spalten)
Links eine **Bread crumb Darstellung des CWP**
Also z.B. /Projekte/Haus/**Dach**/
Wobei das CWP vielleicht irgendwie hervorgehoben ist.
Trennlinie, und rechts davon die Unterprojekte von des CWP.
Also z.B. /Projekte/Haus/**Dach**/ || /Fundraising/, /Webseite/, ...
Ganz rechts vielleicht ein Standardordner /new Project/.
*Je nach Privilegien wird einem /new Project/ angezeigt oder nicht. Der Admin darf vielleicht neue Projekte anlegen, ein normaler Mitarbeiter nicht.*
### Standardfolder
In ganz ähnlicher Weise, wie im Projektbereich werden in der zweiten Zeile die Standardfolder dargestellt:
/finanz/Ausgangsrechnungen/**2025**/ || /01/, /02/, ...
Auch hier je nach Berechtigungen vielleicht ganz rechts ein /new Standardfolder/ Ordner. Dieser führt unauffällig in die Template Bearbeitung. Fügt man hier einen Folder hinzu, wird er **im Template** hinzugefügt.
### eigene, freie Folder
Der User kann sich wie gewohnt überall immer auch eigene Folder anlegen. Auch hier gibt es einen /new Folder/, der je nach Berechtigung angezeigt wird.
Im Unterschied zu den Standardfoldern gibt es hier keinen Breadcrumbbereich. 
Je nach gewünschter Darstellung schließt sich dieser Bereich dem 2. Bereich der Standardfolder rechts an.
Das wäre dann so:
/finanz/Ausgangsrechnungen/**2025**/||/01/, /02/, ...,/12/,/new Standardfolder/, || ,/myFolder/, /myOtherFolder/, /newFolder/ 
### Dateien
Darunter dann der Bereich der Files, der jetzt aber keine Folder mehr anzeigt, sondern nur noch Files, evtl. in der Röntgenansicht.
Auch hier gibt es vielleicht Dinge wie newNote.md, newFile.xls, newFile.doc, ... (das könnte etwas für eine .MyOS/newFiles.md)

Zudem gibt es hier vielleicht auch einen Bereich für **Recent Documents**

# Eine GUI-Idee
In Filebrowsern ist es mitunter stressig und mühsam mit einem File in der Hand den Ort zu finden wo man das File droppen will. 
Sobald man über einen Ordner hoovert, geht der nach kurzer Zeit auf, in langen Listen zu scrollen ist ein Graus, usw.
### Alternative
Ordner öffnen sich nicht nach kurzer Zeit hoovern über einem, sondern erst, wenn man darauf eine Öffnen-Geste ausführt. z.B. einen kleinen Kreis beschreibt.
Mit ähnlichen Gesten könnte ich durch lange Listen scrollen.
So habe ich genug Zeit meinen Zielordner zu finden, ohne, dass ständig unter mir irgendwelche Ordner aufgehen, in die ich gar nicht hinein will.

Und genau dafür könnte das CTD hilfreich sein. Man ändert nicht sein CWD sondern bekommt ein kurzlebiges CTD mit dem man aber auch durch alle Pfade navigieren kann, und sich auch darin die MyOS Magie entfaltet. 
*Vielleicht zieht das GUI aber auch das CWD mit und setzt es nach einem Drop wieder zurück.*
Ein Unterschied zum CWD könnte sein, dass durch das CTD nicht die Desktopumgebung geändert wird.


