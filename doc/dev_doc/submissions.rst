Submissions
===========

Workflow
--------

INGInious manage submission as a group of steps splitted between three major parts : FrontEnd/Client, Backend and Agent.

.. image:: submission_workflow.png
    :align: center

This workflow represents a basic INGInious installation with a basic frontend. For understanding purpose, we represent a workflow where everything is going well.

The process is initialized when the user hits the submission button. This stores initial information about submission in the database and encapsulates the submission within a job.
This first step is finalized with a *ClientNewJob* message sent to the backend with the job included.

The backend stores the job in a waiting queue. When an agent released and the job is the next one in the queue, The job is moved to the running queue, a *BackendNewJob* message is sent to the agent.

Agent treats then the job and once it's over, returns a *AgentJobDone* message to the backend. This one removes job from the running job queue and send a *BackendJobDone* to the client. The client end the process by displaying the result within the frontend and by updating information in the database.

State
-----

Submission is represented as a dictionary from the database. Easy to share and structured.
The concept of Submission have no specific object class in INGInious but has no necessity of that.
Submission come with an interesting property : State.

State is dynamic property that lets you store data related to the submission.
State can be viewed as a bag. You can transport things with no condition about what is in the bag. 
You can set state with basic or complex data types.

State can also be used in the frontend part because it has a task input property. You can so, with basic Javascript, use this.

Evaluation
----------

Submission evaluation is possible in two different ways : By evaluating the best one or the last one.
First one takes the max grade submission.
Second one takes the last submission.
As main part of the evaluation is done within the backend with only one submission, the selection part is done on frontend part.
Evaluation workflow is 