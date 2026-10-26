Who is allowed to see your files? Who is allowed to change them? Especially in teams and when you work together with others, it can be important to protect folders and files from unauthorized access.

That's what *access rights* or *permissions* are about.
Companies pay high salaries to system administrators who manage these permissions with scripts and complicated tools to keep everything safe and in order.

Linux is well known for its very good and strict access rules. That made it the first choice for servers and huge computer clusters. Let's face it: the whole internet runs on Linux. By the way: did you notice that you are working on a Linux machine here?

Let's keep it short and simple. Imagine you want to allow your finance department to read and write in your /04_Finance/ folders. That's just ONE entry in the /04_Finance/ folder of your template, and you're done. From now on, your finance department only sees the folders and files it is allowed to see. They should be able to read /01_Info/ too? No problem. Can you imagine how much this simplifies things?

The most modern and flexible way to manage access rights is so-called *Access Control Lists* (ACLs). In principle these are lists that determine for each folder and each file who may read it, write it, execute it, copy it, create new files in it ... and of course WHO may change these lists. *Roles* that you can define make everything a bit easier. But the real game changer is the way we have implemented it.

We really don't want to bore you with these rather special things here, but they are important. Good to know: it's all implemented, and easier to use than ever.

If you want to dive deeper, you'll find some exercises in this lesson.

[Let's move on!](<../Lesson12/Filters.md>)
