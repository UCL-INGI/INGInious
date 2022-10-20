FROM ubuntu:22.04

RUN apt-get update && apt-get -y install python3 python3-pip

WORKDIR /inginious
COPY inginious/common/ inginious/common/
COPY inginious/__init__.py inginious/
COPY inginious/agent/__init__.py inginious/agent/
COPY inginious/agent/mcq_agent/ inginious/agent/mcq_agent/
COPY inginious-agent-mcq .

COPY agent-mcq.setup setup.py
RUN pip3 install .

CMD ["sh", "-c", "python3 inginious-agent-mcq ${BACKEND}"]
