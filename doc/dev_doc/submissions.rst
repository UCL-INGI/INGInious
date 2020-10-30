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
As main part of the evaluation is done within the backend with only one submission, the selection part is done on frontend part.
If the user run a new submission and that it suits with the evaluation, the submission id is store in database in the user task collection.
The evaluation part really starts when the job is treated by the agent. The agent receives a *BackendNewJob* message and have to handle it. It starts its new_job function.
For MCQ agent, it starts by getting files from task and course file system and the translation files. Then it loops over the question and calculate the number of good answers to return the correct feedback.
For Docker agent, it start by synchronously generate the needed element. It begins with the file system, copying files (especially task files and $common files) and creating the container. It continues by adding new info of the new container and then of course starts this one.
All this work is done within the Asyncio event loop.
once this is done, a safe task (for the agent) is generated for handling the running container. When run() ends, these tasks are automatically cancelled.
The handling of the container is manage through a socket. Messages with data are sent to the container with the run command to evaluate the code. 
Container will then respond with three possible message: student_container, ssh or result.
The first one starts a new student container.
The second one, returns the information for a ssh connection.
The last one, of course, return the results of the run command.
The first two message will generate new action ( create a safe task for the student_container or create a job for ssh info)
The last one will simply set the results and send them back to the frontend for the display part.