Groups & Audiences
==================

Those two structure lets teacher manage the course easily by defining his needs.
By default, a course contains neither audience nor group.
Depending on the needs, it will be recommend to use audience or group. But both can be used together as well.

Audiences
---------

Based on a description, an audience is a subset of students. This subset have no specific size. A list of tutors can be set to see the audience.

This structure is stored as a collection into the database. Audiences are available on frontend side only.

Here is database structure description:

.. code-block:: JSON

    {
        "_id" : "The id of the audience",
        "courseid" : "The id of the course",
        "students" : "The list of students based on user_id",
        "tutors" : "The list of tutors based on user_id",
        "description" "The audience description"

    }



Groups
------

Groups are also subset of students based on a description. As this structure can be used for submission,
it's important to notice that groups are frontend structure.
Backend doesn't know group. It's a table on frontend level.

Here is database structure description:

.. code-block:: JSON

    {
        "_id" : "The id of the group",
        "courseid" : "The id of the course",
        "students" : "The list of students based on user_id",
        "tutors" : "The list of tutors based on user_id",
        "description" "The group description"
    }