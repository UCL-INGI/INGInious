Hook guide
==========

INGInious provides, in the backend and in the frontend, a hook system.
It allows plugins to get additionnal information about what is happening inside INGInious.

Hooks in fact call callback functions that you indicated with the addHook method from HookManager.

Please note that all hooks may be called by another thread, so all actions done into a hook have to be thread-safe.

List of hooks
-------------

Each hook available in INGInious is described here, starting with its name and parameters.
*job_manager_init_done* (*job_manager*)
	Called when a JobManager instance is inited. *job_manager* is the instance that was inited.
	This hooks cannot be used by the plugins, as the backend is inited before the plugins.
*job_manager_exit* (*job_manager*)
	Called when a JobManager received the exit signal, before the JobManager exits.
*new_job* (*jobid*, *task*, *statinfo*, *inputdata*)
	Called when a job was just submitted. *task* contains a Task object,
	*statinfo* is a dictionnary containing various informations about the job.
	*inputdata* contains the answers that were submitted to INGInious.
*job_ended* (*jobid*, *task*, *statinfo*, *results*)
	Called when a job has ended. *task* contains a Task object,
	*statinfo* is a dictionnary containing various informations about the job.
	*results* contains the results of the job.
*new_submission* (*submissionid*, *submission*, *jobid*, *inputdata*)
	Called when a new submission is received.
	*inputdata* contains the answers that were submitted to INGInious.
	Please note that the *job* is not yet send to the backend when this hook is called (so *new_submission* is called before *new_job*),
	pay also attention that a submission is the name given to a job that was made throught the frontend.
	It implies that jobs created by plugins will not call *new_submission* nor *submission_done*.
*submission_done* (*submission*, *job*)
	Called when a submission has ended. The submissionid is contained in the dictionnary submission, under the field *_id*.
	(submission_done is called after job_ended)