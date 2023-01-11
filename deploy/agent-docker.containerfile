FROM inginious/inginious-base

COPY inginious/agent/__init__.py inginious/agent/
COPY inginious/agent/docker_agent/ inginious/agent/docker_agent/
COPY inginious-agent-docker .

RUN dnf install -y gcc python39-devel

COPY deploy/agent-docker.setup setup.py
RUN pip3 install .

CMD ["sh", "-c", "python3 inginious-agent-docker ${BACKEND} --tmpdir=/tmp/agent_data/"]
