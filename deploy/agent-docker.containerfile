FROM inginious/inginious-base

COPY inginious/agent/__init__.py inginious/agent/
COPY inginious/agent/docker_agent/ inginious/agent/docker_agent/
COPY inginious-agent-docker .

COPY deploy/agent-docker.setup setup.py
RUN pip3 install .

CMD ["sh", "-c", "python3 inginious-agent-docker ${BACKEND}"]
