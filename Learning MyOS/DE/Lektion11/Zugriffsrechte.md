Wer darf deine Dateien sehen? Wer darf sie ändern? Besonders in Teams und bei Zusammenarbeit ist es extrem wichtig, Ordner und Dateien vor unbefugtem Zugriff zu schützen.

Darum geht es bei *Zugriffsrechten* oder *Berechtigungen*.
Unternehmen zahlen riesige Gehälter an Sys-Admins, die diese Berechtigungen mit Skripten und komplizierten Tools verwalten, um alles sicher und ordentlich zu halten.

Linux ist bekannt für seine sehr guten und starken Zugriffsrichtlinien, die es zur ersten Wahl für den Aufbau von Servern und großen Computer-Clustern gemacht haben. Sehen wir der Wahrheit ins Auge: Das ganze Internet läuft auf Linux. Übrigens: Hast du bemerkt, dass du hier auf einer Linux-Maschine arbeitest?

Halten wir es kurz und einfach. Stell dir vor, du willst deiner Finanzabteilung die Berechtigung geben, in deine /finance/-Ordner zu lesen und zu schreiben. Es ist nur EIN Eintrag in deinem /finance/-Vorlagen-Ordner und du bist fertig. Von jetzt an sieht deine Finanzabteilung nur die Ordner und Dateien, die sie sehen darf. Du willst, dass sie auch /infos/ lesen können? Kein Problem. Kannst du dir vorstellen, wie das die Dinge erheblich erleichtert?

Allerdings: Die modernste und flexibelste Art, Zugriffsrechte zu verwalten, sind sogenannte *Access Control Lists* (ACLs). Das sind im Prinzip Listen, die für jeden Ordner oder jede Datei festlegen, wer sie lesen, schreiben, ausführen, kopieren, neue Dateien erstellen darf ... und natürlich WER diese Listen ändern darf. Alles wird etwas einfacher durch „*Rollen*", die du definieren kannst. Aber der eigentliche Game Changer kommt mit unserer Implementierung.

Wir wollen dich hier wirklich nicht mit diesen Interna belasten, aber es ist wichtig. Gut zu wissen: Es ist alles implementiert und einfacher zu nutzen als je zuvor.

Wenn du tiefer einsteigen willst, findest du in dieser Lektion einige Übungen.

[[MyOS/Learning MyOS/DE/Lektion12/Perspektiven|Weiter!]]
