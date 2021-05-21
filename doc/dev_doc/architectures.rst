INGInious Architecture
======================

.. _frontend:

Frontend
--------

Frontend architecture is mainly based on web.py framework. 
Basically the python code is in the root folder. A ``template`` folder groups HTML templates used by the framework and a ``static`` folder contains CSS and JS files.

Also a ``page`` directory contains all the page definitions. Those definitions are Python class that implement GET and POST methods. This is not the only job of those class but it's the main one.

Some important python modules (related to frontend development) are defined in the frontend like:

- User manager
- Submission manager
- Plugin manager
- Tasks and Courses factories
- webdav
- ...

Those modules manage object use only in the frontend. They are never shared with the backend or common parts.

In addition of this a ``plugins`` package contains all the plugins that are used by the instance. Those plugins must first be defined in the configuration file.

Besides, a ``task_dispensers`` package has been add to ensure the distribution of question through the frontend. This add extra feature to improve the task listing for a course.

Finally, a ``tests`` package gather all the tests write to ensure the good behaviour of the frontend.

.. _backend:

Backend queue
-------------

Backend package architecture is quite simple to understand are there are two important files. 

First one is ``topic_priority_queue.py`` that defines a queue data structure based on topics. 

The other one is ``backend.py`` which define the all backend logic base on message passing. Backend uses the topic priority queue to handle requests.

.. _agent:

Agent
-----

Agent package is split into python subpackages : Docker and MCQ.

MCQ subpackage defines a class object that implements the MCQ Agent. This comes with translation configuration files.

Docker subpackage also defines a class object that implements Docker Agent. An interface to Docker is also defined as utils for Docker mangement. Finally a timeout interface is also declared to especially manage timeout in agent.