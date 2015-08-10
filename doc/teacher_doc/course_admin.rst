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

Classrooms and groups
---------------------

Classrooms are useful to administratively separate students following the
same course. Classrooms offer separate statistics to help the teacher identify
problems students may encounter in this particular context. Submission
groups can be set in classrooms. These groups define a set of users that
will submit together. Their submissions will contain as authors all the
students that were members of the group at submission time.

Students in one classroom can collaborate together if the teacher allow
them to, and cannot collaborate with students from another classroom.
If you want students from different classrooms to work together in one
submission group, maybe INGInious classrooms are not useful for you and
you should only consider groups in one default classroom.

Classroom creation/edition
``````````````````````````

Classrooms have to be created and edited from the web app in the course
administration. In the classroom list view, specify a classroom description,
and click on "Create new classroom". The newly created classroom will appear
in the list.

To edit a classroom, click on the quick link "Edit classroom" located on the
right side of the table. You'll be able to change the classroom description,
the associated teaching staff, and to specify the (grouped) students.
Assigning tutors will help them to retrieve their classroom statistics.

The student list is entirely managed by drag-and-drop. You can create
a new group on the same page, set its maximum size, and drag-and-drop
ungrouped students or already grouped students in the newly created group.

Classroom upload
````````````````

You can generate your classroom structure with an external tool and then
upload it on INGInious. A YAML file of this structure is required :

::

    description: Classroom description
    tutors:
            - tutor1
            - tutor2
    students:
            - user1
            - user2
    groups:
            - size: 2
              students:
                    - user1
                    - user2

-   *description* is a string and corresponds to your class description

-   *tutors* is a list of strings representing the usernames of the
    assigned classroom tutors.

-   *students* is a list of strings representing the usernames of the
    classroom students.

-   *groups* is a list of group structures containing the following elements :

    *size*
        the maximum group size
    *students*
        the list of student usernames in this group


Group attribution
`````````````````

If you do not really matter the way students are grouped together, you can
set empty groups with maximum size and let the students choose their groups
themselves. Just check the option in the course settings to allow them to group
together. When submissions will be retrieved, the group members will be displayed
as the authors as with staff-grouped students.