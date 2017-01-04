Creating plugins
================

INGInious provides a simple plugin system that allow to register some hooks to extend existing features, create new
frontend pages and features, and add new authentication methods.

Hooks actually call callback functions that you indicated with the ``add_hook`` method from ``HookManager``. Please
note that all hooks may be called by another thread, so all actions done into a hook have to be thread-safe.

Tutorial
--------

The following code adds a new page displaying ``This is a simple demo plugin`` on the ``/plugindemo`` location.

.. code-block:: python

    class DemoPage(object):
        """ A simple demo page showing how to add a new page """

        def GET(self):
            """ GET request """
            return "This is a simple demo plugin"


    def init(plugin_manager, course_factory, client, plugin_config):
        """ Init the plugin """
        plugin_manager.add_page("/plugindemo", DemoPage)


The plugin is initialized by the plugin manager, which is the frontend-extended hook manager, by calling method ``init``.
This method takes four arguments:

- ``plugin_manager`` which is the plugin manager singleton object. The detailed API is available at
  :ref:`inginious.frontend.common.plugin_manager`. Please note that ``PluginManager`` inherits from
  :ref:`inginious.common.hook_manager`.

- ``course_factory`` which is the course factory singleton object, giving you abstraction to the tasks folder. The detailed
  API is available at :ref:`inginious.common.course_factory`.

- ``client`` which is the INGInious client singleton object, giving you access to the backend features, as launching
  a new job. The detailed API is available at :ref:`inginious.client.client`.

- ``plugin_config`` which is a dictionary containing the plugin configuration fields set in your ``configuration.yaml``
  file. For instance, configuration:
  ::

        plugins:
            - plugin_module: inginious.frontend.webapp.plugins.demo
              param1: "value1"

  will generate the following ``plugin_config`` dictionary :
  ::

        {"plugin_module": "inginious.frontend.webapp.plugins.demo", "param1": "value1"}


The remaining INGInious classes can be used from your plugins using correct imports. The ``init`` method gives you access
to the different singletons used by INGInious which are instantiated at boot time. For instance, ``LTIPage`` class can
be used as base for a new LTI page.

The ``plugin_module`` configuration parameter corresponds to the Python package in which the ``init`` method is found.
A demonstration plugin is found in the ``inginious.frontend.webapp.plugins.demo``. You do not need to include your plugin
in the INGInious sources. As long as your plugin is found in the Python path, it will remain usable by INGInious.

List of hooks
-------------

You may be interested to generate some actions useful for your plugins before or after some INGInious events. You
would therefore need to add a hook method. This can be done using the ``add_hook`` method of package
:ref:`inginious.frontend.common.plugin_manager`. For instance, the following plugin :

.. code-block:: python

    import logging

    def submission_done(submission, archive, newsub):
        logging.getLogger("inginious.frontend.webapp.plugins.demo").info("Submission " + str(submission['_id']) + " done.")

    def init(plugin_manager, course_factory, client, plugin_config):
        """ Init the plugin """
        plugin_manager.add_hook("submission_done", submission_done)

will log each submission id that has been returning from the backend.

Each hook available in INGInious is described here, starting with its name and parameters. Please refer to the complete
:ref:`inginious.frontend.common` package documentation for more information on the data returned by those hooks.

``css``
    Returns : List of path to CSS files.

    Used to add CSS files in the header. 
    Should return the path to a CSS file (relative to the root of INGInious).
``course_admin_menu`` (``course``)
    ``course`` : :ref:`inginious.frontend.common.courses.FrontendCourse`

    Returns : Tuple (link, name) or None.

    Used to add links to the administration menu. This hook should return a tuple (link,name) 
    where link is the relative link from the index of the course administration.
    You can also return None.
``main_menu`` (``template_helper``)
    ``template_helper`` : :ref:`inginious.frontend.common.template_helper.TemplateHelper`

    Returns : HTML or None.

    Allows to add HTML to the menu displayed on the main (course list) page. ``template_helper`` is an object
    of type TemplateHelper, that can be useful to render templates.
``course_menu`` (``course``, ``template_helper``)
    ``course`` : :ref:`inginious.frontend.common.courses.FrontendCourse`

    ``template_helper`` : :ref:`inginious.frontend.common.template_helper.TemplateHelper`

    Returns : HTML or None.

    Allows to add HTML to the menu displayed on the course page. Course is the course object related to the page. ``template_helper`` is an object
    of type TemplateHelper, that can be useful to render templates.
``task_menu`` (``course``, ``task``, ``template_helper``)
    ``course`` : :ref:`inginious.frontend.common.courses.FrontendCourse`

    ``task`` : :ref:`inginious.frontend.common.tasks.FrontendTask`

    ``template_helper`` : :ref:`inginious.frontend.common.template_helper.TemplateHelper`

    Returns: HTML or None.

    Allows to add HTML to the menu displayed on the course page. ``course`` is the course object related to the page. ``task``
    is the task object related to the page. ``template_helper`` is an object of type TemplateHelper, that can be useful to render templates.
``welcome_text`` (``template_helper``)
    ``template_helper`` : :ref:`inginious.frontend.common.template_helper.TemplateHelper`

    Returns : HTML or None.

    Allows to add HTML to the login/welcome page. ``template_helper`` is an object
    of type TemplateHelper, that can be useful to render templates.
``javascript_header``
    Returns : List of path to Javascript files.

    Used to add Javascript files in the header. 
    Should return the path to a Javascript file (relative to the root of INGInious).
``javascript_footer``
    Returns : List of path to Javascript files.

    Used to add Javascript files in the footer. 
    Should return the path to a Javascript file (relative to the root of INGInious).
``course_accessibility`` (``course``, ``default``)
    Returns: inginious.frontend.webapp.accessible_time.AccessibleTime

    ``course`` : inginious.common.courses.Course

    ``default`` : Default value as specified in the configuration

    Overrides the course accessibility.
``task_accessibility`` (``course``, ``taskid``, ``default``)
    Returns: inginious.frontend.webapp.accessible_time.AccessibleTime

    ``course`` : inginious.common.courses.Course

    ``task`` : inginious.common.tasks.Task

    ``default`` : Default value as specified in the configuration

    Overrides the task accessibility
``task_limits`` (``course``, ``taskid``, ``default``)
    Returns: Task limits dictionary

    ``course`` : inginious.common.courses.Course

    ``task`` : inginious.common.tasks.Task

    ``default`` : Default value as specified in the configuration

    Overrides the task limits
``task_context`` (``course``, ``taskid``, ``default``)
    Returns: inginious.frontend.common.parsable_text.ParsableText

    ``course`` : inginious.common.courses.Course

    ``task`` : inginious.common.tasks.Task

    ``default`` : Default value as specified in the configuration

    Overrides the task context
``task_network_grading`` (``course``, ``taskid``, ``default``)
    Returns: True or False

    ``course`` : inginious.common.courses.Course

    ``task`` : inginious.common.tasks.Task

    ``default`` : Default value as specified in the configuration

    Overrides the task network-enable option
``new_submission`` (``submissionid``, ``submission``, ``inputdata``)
    ``submissionid`` : ObjectId corresponding to the submission recently saved in database.

    ``submission`` : Dictionary containing the submission metadata.

    ``inputdata`` : Dictionary containing the raw input data entered by the student. Each key corresponding to the
    problem id.

    Called when a new submission is received.
    Please note that the job is not yet send to the backend when this hook is called,
    pay also attention that a submission is the name given to a job that was made through the frontend.
    It implies that jobs created by plugins will not call ``new_submission`` nor ``submission_done``.
``submission_done`` (``submission``, ``archive``, ``newsub``)
    ``submission`` : Dictionary containing the submission metadata.

    ``archive`` : Bytes containing the archive file generated by the job execution. This can be ``None`` if no archive
    is generated (for einstance, in MCQ).

    ``newsub`` : Boolean indicating if the submission is a new one or a replay.

    Called when a submission has ended. The submissionid is contained in the dictionary submission, under the field ``_id``.
``template_helper`` ()
    Returns : Tuple (name,func)

    Adds a new helper to the instance of TemplateHelper. Should return a tuple (name,func) where name is the name that will
    be indicated when calling the TemplateHelper.call method, and func is the function that will be called.