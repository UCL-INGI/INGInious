INGInious
=========

This container runs INGInious(frontend, backend and agent) directly in docker.

This container needs:

- The docker daemon has to be accessible inside the container. If you access the docker daemon via a socket, you will have to share it with
  ````
  -v /var/run/docker.sock:/var/run/docker.sock
  ````
  If you access it via a tcp, you should define the DOCKER_HOST environment variable correctly inside the container:
  ````
  -e DOCKER_HOST=$DOCKER_HOST
  ````

- The container needs a shared volume that contains
  - configuration.json
  - configuration-agent.json
  - the "tasks" folder

  It should be mounted on /INGInious-local
  ````
  -v /absolute/path/to/your/shared/dir:/INGInious-local
  ````

- An access to /sys/fs/cgroup (used by Docker)
  ```
  -v /sys/fs/cgroup:/sys/fs/cgroup
  ```

Starting only the agent
-----------------------

By default, the container launches MongoDB, the frontend of INGInious and an agent.
If you want to only start an agent, add ``` python /INGInious/app_agent.py ``` to the end of ``` docker run ```.

Examples
--------

- CentOS 7

  ````bash
  $ docker run -v /var/run/docker.sock:/var/run/docker.sock -v /home/gderval/INGInious:/INGInious-local -v /sys/fs/cgroup:/sys/fs/cgroup inginious/inginious
  ````
  
- OS X with docker-osx

  ````bash
  $ eval `docker-osx env`
  $ docker run -e DOCKER_HOST=$DOCKER_HOST -v /Users/gderval/INGInious:/INGInious-local -v /sys/fs/cgroup:/sys/fs/cgroup inginious/inginious
  ````
  Note: ``` -v /sys/fs/cgroup:/sys/fs/cgroup ``` will use the directory from the VM.
