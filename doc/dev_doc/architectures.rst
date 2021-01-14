INGInious Architectures
=======================


Frontend Architecture
---------------------

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


Backend Architecture
--------------------



Agent Architecture
------------------

