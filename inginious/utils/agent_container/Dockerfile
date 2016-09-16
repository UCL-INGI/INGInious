# Download the sources of the agent from github and build the container from it.

FROM centos

RUN \
    yum -y update && \
    yum -y install epel-release && \
    yum -y install docker python34 python34-pip gcc python34-devel git python34-setuptools  && \
    easy_install-3.4 pip && \
    pip3.4 install pytidylib docutils git+https://github.com/tomerfiliba/rpyc.git git+https://github.com/peo3/cgroup-utils.git pyyaml docker-py
    
VOLUME /agent_volume
VOLUME /sys/fs/cgroup

RUN \
    mkdir /agent && \
    mkdir /agent/inginious && \
    touch /agent/inginious/__init__.py && \
    mkdir /agent/inginious/backend && \
    touch /agent/inginious/backend/__init__.py && \
    git clone https://github.com/UCL-INGI/INGInious.git /INGInious && \
    cp -r /INGInious/inginious/common /agent/inginious/common && \
    cp -r /INGInious/inginious/backend/agent /agent/inginious/backend/agent && \
    rm -rf /INGInious

WORKDIR /agent
CMD ["/agent/inginious/backend/agent/start_container_agent.py"]

LABEL agent-version=0.5
