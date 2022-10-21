FROM inginious/inginious-base

COPY inginious/backend/ inginious/backend/
COPY inginious-backend .

COPY deploy/backend.setup setup.py
RUN pip3 install .

CMD ["sh", "-c", "python3 inginious-backend ${AGENT} ${CLIENT}"]
