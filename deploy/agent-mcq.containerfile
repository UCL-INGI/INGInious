FROM inginious/inginious-base

COPY inginious/agent/__init__.py inginious/agent/
COPY inginious/agent/mcq_agent/ inginious/agent/mcq_agent/
COPY inginious-agent-mcq .

COPY deploy/agent-mcq.setup setup.py
RUN pip3 install .

CMD ["sh", "-c", "python3 inginious-agent-mcq ${BACKEND}"]
