# Access rights exercises

In this lesson there is the **Sample Company** with four people: Eva Muster (management), Anna Huber (accounting), Karl Berger (team) and Mia Novak (guest). Who may do what is in one single note: *.MyOS/ACLs.md*.

## 1. Who may enter here?
Open the Sample Company in Scope: **[▶ Open the Sample Company](<myos:open?scope=Sample Company>)**. On the left, under **Access**, you see who may access the folder shown – groups and people, with small arrows: ◂ read, ▸ write. Go into *04_Finance*: now accounting is listed there. Go into *07_Work/Confidential*: the team may not enter here, only the management.
Scope may tell you: "You are not listed in this project. Who are you?" – leave that for now; in exercise 4 you add yourself.

## 2. Through the eyes of a group
Click *Team* on the left: Scope only shows what the team may access. A second click shows everything again.

## 3. One single line
Open *.MyOS/ACLs.md*. *.MyOS* is a hidden folder – in Scope you show it with ⚙ → Scope → Hidden folders. Under **## Guest** it says `- /01_Info/: read`. This one line says: guests may read /01_Info/ – and nothing else.

## 4. Become admin yourself (advanced)
Only an admin may change rights – and in the Sample Company nobody is one yet. In ACLs.md, under **# Users**, write a new line: your user name on this computer (the name of your personal folder under /home), a colon, and *Admin*, for example `maria: Admin`.
Back in Scope, you can now **right-click** a group to change its rights for the folder shown. For example, give the team read access in *04_Finance*. Then look into ACLs.md: exactly one line has been added. MyOS keeps the previous version in *.MyOS/ACLs-history*.

## 5. A new colleague
At the bottom left you now find **+ Person**. Add Lea Wagner and give her the group Team. That, too, is one line in ACLs.md afterwards.

---
Good to know: whether MyOS also enforces the rights is still a switch for developers. In these exercises you see who may do what – MyOS won't hide anything yet.

[Back to the lesson](<Access Rights.md>)
