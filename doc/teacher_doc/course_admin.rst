Course administration
=====================

As a course administrator, you can simply access its management
page by clicking on "Course administration" in the main course page.

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

Student submissions can be downloaded from the *Download submissions* and statistics pages or the submission
inspection page. You are able to only download the set of evaluation submissions (according to the task parameters)
or all the submissions.

Submissions are downloadable as gzip tarball (.tgz) files. You may need some third-party software if your operating
system does not support this format natively. The files contain, for each submissions, a test file
with extension *test* containing the all the submission metadata and the associated archive folder containing all the
files that have been exported using the ``archive`` API (See :ref:`run_file`).

Replaying submissions
`````````````````````
Student submissions can be replayed either from the *Replay submissions* and statistics pages or the
submission inspection page. Different replay scheme are available:

- As replacement of the current student submission result. This is the default scheme for the *Replay submissions* page.
  When replayed, submission input are put back in the grading queue. When the job is completed, the newly computed
  result will replace the old one. This is useful if you want to change the grading scripts during or after the assignment
  period and want all students to be graded the same way. You can replay only the evaluation submission or all submissions.
  However, please note that if replayed, the best submission can be replaced by an older best submission.
- As a personal copy. This mode is only available from the submission inspection page and copy the student input to
  generate a new personal copy. This is useful for debugging if a problem occur with a specific student submission.
  Submission copy is also available with SSH debug mode.

.. WARNING::
    This feature is currently under testing. As the same job queue is used for standard submissions and submission
    replay, it is recommended not to launch huge replay jobs on a very active INGInious instance.


Task edition
------------

All tasks can be edited from the webapp. To access the task editor, just click
on *Edit task* on the task page or from the main administration page.

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

Task files
``````````

Task files can be created, uploaded and modified from the task edition page.
Only text-base files can be edited from the webapp. Binary files can however be uploaded.

The behaviour of the *Move* action is Unix-like : it can be used for renaming files.

.. _groups:

Classrooms and teams
--------------------

Collaborative work and separate students administration are possible in INGInious.
Two models are available:

- *Classrooms and groups* : Classrooms are useful to administratively separate
  students following the same course. They offer separate statistics to
  help the teacher identify problems students may encounter in this particular context.

  Submissions groups can be set in classrooms and define a set of users that
  will submit together. Their submissions will contain as authors all the
  students that were members of the group at submission time. Note that students cannot
  collaborate with students from another classroom. In this case, please consider
  using only teams, as described below.
- *Teams* : Teams are administratively-separated submissions groups. They are
  internally assimilated to classrooms with a unique submission group. They offer
  separate statistics for each submission group.

Choice between these two models can be made in the course settings. Switching from
one model to another will reinitialize the all course structure (that is, students
registration also). Course structures can be backed up if necessary from the
classrooms/teams administration pages.

Creation and edition
````````````````````

Classrooms and teams are created and edited from the web app in the course
administration.

Classrooms and groups
*********************

In the classroom list view, specify a classroom description, and click on
"*Create new classroom*". The newly created classroom will appear in the list.

To edit a classroom, click on the quick link "*Edit classroom*" located on the
right side of the table. You'll be able to change the classroom description,
the associated teaching staff, and to specify the (grouped) students.
Assigning tutors will help them to retrieve their classroom statistics.

The student list is entirely managed by drag-and-drop. You can create
a new group on the same page, set its maximum size, and drag-and-drop
ungrouped students or already grouped students in the newly created group.

Teams
*****

To create a new team, click on "*Edit teams*" simply in the team list view and
press on the "*New team*" button. You'll then be able to specify the team
description, its maximum size, assigned tutors and students. Team edition
works the same way.

The student list is entirely managed by drag-and-drop. Students can be moved
from one team to another by simply moving his name to the new team.

Group/team attribution
``````````````````````

If you do not really matter the way students work together, you can
set empty groups or teams with maximum size and let the students choose their
groups or teams themselves. Just check the option in the course settings to
allow them to gather. When submissions will be retrieved, the group/team members will
be displayed as the authors as with staff-defined groups or teams.

Course structure upload
```````````````````````

You can generate the course classroom or team structure with an external tool
and then upload it on INGInious. This is done with a YAML file, which structure
for classrooms or teams are similar and described below. The course structure
can be upload on the classroom or team list view in the course administration.

Classrooms YAML structure
*************************

::

    -    description: Classroom 1
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
    -    description: Classroom 2
         tutors:
                 - tutor1
                 - tutor2
         students:
                 - user3
                 - user4

-   *description* is a string and corresponds to your class description
-   *tutors* is a list of strings representing the usernames of the
    assigned classroom tutors.
-   *students* is a list of strings representing the usernames of the
    classroom students.
-   *groups* is a list of group structures containing the following elements :

    - *size*: the maximum group size
    - *students*:  the list of student usernames in this group

Teams YAML structure
********************

::

    -    description: Team 1
         tutors:
                 - tutor1
                 - tutor2
         students:
                 - user1
                 - user2
    -    description: Team 2
         tutors:
                 - tutor1
                 - tutor2
         students:
                 - user3
                 - user4

-   *description* is a string and corresponds to your team description
-   *tutors* is a list of strings representing the usernames of the
    assigned team tutors.
-   *students* is a list of strings representing the usernames of the
    team students.

Backup course structure
```````````````````````

Course structures (classrooms or teams) can be exported for backup or manual
edition via the classroom/team list page in the course administration pages.
Simply click on the "*Download structure*" button. The download file will have
the same format as described above.