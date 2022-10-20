FROM ubuntu:22.04

RUN apt-get update && apt-get -y install python3 python3-pip

WORKDIR /inginious
COPY inginious/common/ inginious/common/
COPY inginious/agent/__init__.py inginious/agent/
COPY inginious/agent/docker_agent/ inginious/agent/docker_agent/
COPY inginious-agent-docker .

COPY agent-docker.setup setup.py
RUN pip3 install .


CMD ["sh", "-c", "python3 inginious-agent-docker ${BACKEND}"]
