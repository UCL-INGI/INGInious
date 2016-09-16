Hook guide
==========

INGInious provides, in the backend and in the frontend, a hook system.
It allows plugins to get additionnal information about what is happening inside INGInious.

Hooks in fact call callback functions that you indicated with the addHook method from HookManager.

Please note that all hooks may be called by another thread, so all actions done into a hook have to be thread-safe.

List of hooks
-------------

Each hook available in INGInious is described here, starting with its name and parameters.
``css``
    Used to add CSS files in the header. 
    Should return the path to a CSS file (relative to the root of INGInious).
``course_admin_menu`` (``course``)
    Used to add links to the administration menu. This hook should return a tuple (link,name) 
    where link is the relative link from the index of the course administration.
    You can also return None.
``course_menu`` (``course``,``template_helper``)
    Allows to add HTML to the menu displayed on the course page. Course is the course object related to the page. ``template_helper`` is an object
    of type TemplateHelper, that can be useful to render templates.
    Should return HTML or None.
``task_menu`` (``course``,``task``,``template_helper``)
    Allows to add HTML to the menu displayed on the course page. ``course`` is the course object related to the page. ``task``
    is the task object related to the page. ``template_helper`` is an object of type TemplateHelper, that can be useful to render templates.
    Should return HTML or None.
``javascript_header``
    Used to add Javascript files in the header. 
    Should return the path to a Javascript file (relative to the root of INGInious).
``javascript_footer``
    Used to add Javascript files in the footer. 
    Should return the path to a Javascript file (relative to the root of INGInious).
``job_ended`` (``jobid``, ``task``, ``statinfo``, ``results``)
   Called when a job has ended. ``task`` contains a Task object,
   ``statinfo`` is a dictionnary containing various informations about the job.
   ``results`` contains the results of the job.
``modify_task_data`` (``course``, ``taskid``, ``data``)
    Allows to modify the task description before the initialisation of the Task object.
    Changes are not saved to disk.
``new_job`` (``jobid``, ``task``, ``statinfo``, ``inputdata``)
    Called when a job was just submitted. ``task`` contains a Task object,
    ``statinfo`` is a dictionnary containing various informations about the job.
    ``inputdata`` contains the answers that were submitted to INGInious.
``new_submission`` (``submissionid``, ``submission``, ``jobid``, ``inputdata``)
    Called when a new submission is received.
    ``inputdata`` contains the answers that were submitted to INGInious.
    Please note that the ``job`` is not yet send to the backend when this hook is called (so ``new_submission`` is called before ``new_job``),
    pay also attention that a submission is the name given to a job that was made throught the frontend.
    It implies that jobs created by plugins will not call ``new_submission`` nor ``submission_done``.
``submission_done`` (``submission``, ``result``, ``grade``, ``problems``, ``tests``, ``custom``, ``archive``)
    Called when a submission has ended. The submissionid is contained in the dictionnary submission, under the field ``_id``.
    (submission_done is called after job_ended)
``template_helper`` ()
    Adds a new helper to the instance of TemplateHelper. Should return a tuple (name,func) where name is the name that will
    be indicated when calling the TemplateHelper.call method, and func is the function that will be called.