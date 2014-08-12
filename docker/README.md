INGInious
=========

This container runs INGInious directly in docker.

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
  - the "tasks" folder
  It should be mounted on /INGInious-local
 
