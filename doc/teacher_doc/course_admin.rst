Course administration
=====================

As a course administrator, you can simply access its management
page by clicking on "Manage" in the task list page the course.

Students submissions
--------------------
Statistics over students submissions are largely available in INGinious,
and all the files related to them are stored and can be downloaded.

General overview
````````````````
The administration page gives you several global list views :

- All the tasks of a course, with  the number of students who viewed the
  at least one time, who tried and the number of tries, as well as the
  number of students who succeded the task. This view is the first
  displayed when you click on "Manage" to enter the administration.
- All the students of a course, with the number of tasks tried and done,
  as well as its global progression. This view can be accessed by
  switching to "View students" in the main administration page.
- All the students who tried a given task, if they succeded it, and the
  number of submissions they did. You can show these information by
  clicking "View student list" on the main administration page or by
  clicking "Satistics" on the task page.
- All the tasks tried by a given student, if (s)he succeded it and the
  number of submissions (s)he did. These information can be displayed by
  clicking "View" in the students list of a course.
- All the submissions made by a student for a given tasks, with date of
  submission and the global result. Submissions can be displayed by
  clicking "View submissions" in tasks lists.

All the tables can be downloaded in CSV format to make some further
treatment in your favourite spreadsheet editor.

Downloading submissions
```````````````````````
All views allows you to download a set of submissions, from a specific
submission to all submissions related to one course. You can choose
to download either the last (correct if succeded) submissions or all the
submissions available.

Submissions are downloadable as gzip tarball (.tgz) files. You may need
some third-party software if your operating system does not support this
format natively. The files contain, for each submissions, a test file
with extension *test* and

Task edition
------------

All tasks can be edited on-line. To access the task editor, just click
on "Edit task" on the task page or from the main administration page.
Task problems containing boxes are not graphically editable due to
their high modularity. These kinds of problem editable on-line in JSON
format.

Adding/removing problems
````````````````````````
Adding and removing problems are very easy in the task editor, go to the
end of the page or click on the quick link "Add subproblem". You'll then
be brought to a new form asking a problem-id (alphanumerical characters)
and a problem type.

To make a more complex question with boxes, choose "custom" problem and
write the JSON problem description as described in the task file format.

When editing a multiple choice problem, you're asked if the student is
shown a multiple-answers- or single-answer-problem and which of the
possible choices is (are) good answer(s).

Uploading task files
````````````````````
