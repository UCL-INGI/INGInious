FROM centos

RUN \
    yum -y update && \
    yum -y install epel-release && \
    yum -y install docker python-pip gcc python-devel && \
    pip install pytidylib docutils rpyc cgroup-utils pyyaml

# temp workaround for Docker 1.7 (TODO: revert me!)
RUN \
    yum -y install git && \
    git clone https://github.com/GuillaumeDerval/docker-py.git /docker-py && \
    cd /docker-py && \
    pip install . && \
    cd .. && \
    rm -Rf /docker-py
    
VOLUME /agent_volume
VOLUME /sys/fs/cgroup

ADD common /agent/common
ADD backend_agent /agent/backend_agent
WORKDIR /agent
CMD ["/agent/backend_agent/start_container_agent.py"]

LABEL agent-version=0.2
