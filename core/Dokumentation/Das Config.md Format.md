Im /.MyOS/-Ordner aber auch ausserhalb in beliebigen Foldern können Config.md-Files liegen, die vom System verwendet werden, um MyOS-Funktionalitäten bereitzustellen.
Beispiele: Templates.md, ACLs.md, Tags.md, Desk.md, usw.

Diese Config.md werden in einer gewissen Weise von MyOS interpretiert:

1. **Überschriften 1** werden wie einzelne Files interpretiert. Das ermöglicht uns 2, mehr oder alle Config-Files in nur einem einzigen File zusammenzufassen.
   
   Also 2 getrennte Files (Tags.md, Templates.md) haben den gleichen Effekt wie eine Config.md, die so aufgebaut ist: 
# Tags
   * red: important
   * yellow: recent
   * green: done
		
# Templates
* Standard
* Website
Überschriften der Ebene # 1 können also im Weiteren als ebensolche oder als einzelne MD-Files verstanden werden. 
  


2. Einzelne Worte oder Listen von Keywords direkt nach Filebeginn oder nach einer BELIEBIGEN Überschrift werden als Properties oder Listen interpretiert. Eine Leerzeile, ein beliebiger Text bricht diese Interpretation.
   
# Templates
Standard
wird als {Templates: Standard} interpretiert.

# Templates
* Standard
* Website
wird als {Templates: [Standard, Website]}

# Templates

* Standard
* Website
wird als NaN interpretiert.

Es ist noch nicht klar festgelegt, ob einzelne Worte (Properties) nicht auch immer als Listen mit nur einem Eintrag interpretiert werden sollen. Könnte einfacher sein. Also:

# Templates
Standard
wird als {Templates: [Standard]} interpretiert.


3. Auch Zeilen mit Keword: Liste, Liste2, Liste3 werden als Properties oder Listen interpretiert.

# ACLs
* Admin: Alfred
* Member: Bertha, Christian, ... 
wird als {ACLs:[{Admin:[Alfred], Member: [Bertha, Christian, ...]}]} interpretiert.

Der Interpreter oder Parser kann also ein solches Objekt bauen und zurückgeben: ACLs.Admin

Alles sehr ähnlich zu YAML aber ohne Einrückungen und über Überschriften strukturiert.


4. Auch Zwischenüberschriften sind erlaubt.
# Templates
* Standard
* Website

#### inherit
fix

könnte über Templates.inherit abgefragt werden.
