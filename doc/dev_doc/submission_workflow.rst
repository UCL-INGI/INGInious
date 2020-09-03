Submission workflow
===================

INGInious manage submission as a group of steps splitted between three major parts : FrontEnd/Client, Backend and Agent.

.. image:: /dev_doc/submission_workflow.png
    :align: center

This workflow represents a basic INGInious installation with a basic frontend. For understanding purpose, we represent a workflow where everything is going well.

The process is initialized when the user hits the submission button. This stores initial information about submission in the database and encapsulates the submission within a job.
This first step is finalized with a *ClientNewJob* message sent to the backend with the job included.

The backend stores the job in a waiting queue. When an agent released and the job is the next one in the queue, The job is moved to the running queue, a *BackendNewJob* message is sent to the agent.

Agent treats then the job and once it's over, returns a *AgentJobDone* message to the backend. This one removes job from the running job queue and send a *BackendJobDone* to the client. The client end the process by displaying the result within the frontend and by updating information in the database.