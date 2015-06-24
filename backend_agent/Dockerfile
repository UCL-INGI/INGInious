FROM centos

LABEL agent-version=0.1

RUN \
   yum -y update && \
   yum -y install epel-release && \
   yum -y install docker python-pip gcc python-devel && \
   pip install pytidylib docker-py docutils rpyc cgroup-utils

RUN pip install pyyaml

ADD common /agent/common
ADD backend_agent /agent/backend_agent
WORKDIR /agent

VOLUME /agent_volume
VOLUME /sys/fs/cgroup

CMD ["/agent/backend_agent/start_container_agent.py"]