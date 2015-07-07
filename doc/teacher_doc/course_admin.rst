Course administration
=====================

NOTE: this page is old and needs a complete rewrite.

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
- All the students/groups of a course, with the number of tasks tried and done,
  as well as its global progression for students. This view can be accessed by
  switching to "Students"/"Groups" in the main administration page.
- All the students/groups who tried a given task, if they succeded it, and the
  number of submissions they did. You can show these information by
  clicking "View results" on the main administration page or by
  clicking "Statistics" on the task page.
- All the tasks tried by a given student/group, if (s)he/they succeded it and the
  number of submissions (s)he/they did. These information can be displayed by
  clicking "View" in the student/group list of a course.
- All the submissions made by a student/group for a given tasks, with date of
  submission and the global result. Submissions can be displayed by
  clicking "View submissions" in tasks lists.

All the tables can be downloaded in CSV format to make some further
treatment in your favourite spreadsheet editor.

More information about groups_ possibilities can be found below.

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
their high modularity. These kinds of problem editable on-line in YAML
format.

Adding/removing problems
````````````````````````
Adding and removing problems are very easy in the task editor, go to the
end of the page or click on the quick link "Add subproblem". You'll then
be brought to a new form asking a problem-id (alphanumerical characters)
and a problem type.

To make a more complex question with boxes, choose "custom" problem and
write the YAML problem description as described in the task file format.

When editing a multiple choice problem, you're asked if the student is
shown a multiple-answers- or single-answer-problem and which of the
possible choices is (are) good answer(s).

Uploading task files
````````````````````

.. _groups:

Group work
----------

Students may sometimes be allowed to work in groups. In this case, they
are used to submit one common work. INGInious integrates a group
management solution to ease the teacher to correct these grouped works

What is a group ?
`````````````````

A group in INGInious is defined as follow: it consists in a possibly
changing association of users that make submissions together, and an
identifier/description that enables the easy retrieval of submissions.
That is, every submission is accounted to every student that was member
of the group at the submission time, and the submissions associated to
a group are linked to its identifier and may not be made by the same
association of users if the group changed at some time.
It is therefore recommended to make only minor changes to a created group.

Activating group work
`````````````````````

Group work can be enabled and disabled during the period of the course.
Statistics will be kept. However, these group statistics are only
available when group work is enabled. To enable group work in the course
settings, switch the submission mode to "Per groups" in the course
settings.

Groups can be formed by the course administrators or by the students
at the registration time. This option can be set in the course settings.
If the option is set, students will be asked to select a group among
the remaining non-full groups at the registration time.

Group creation/edition
``````````````````````

Groups have to be created and edited from the frontend in the course
administration. In the group list view, specify a group description,
and click on "Create new group". The newly created group will appear
in the list.

To edit a group, click on the quick link "Edit group" located on the
right side of the table. You'll be able to change the group
description and to specify the maximum group size, the student list
(from the registered student list of your course) and the assigned
tutors/supervisors (from the teaching staff). Assigning tutors will
help them to retrieve their group statistics.