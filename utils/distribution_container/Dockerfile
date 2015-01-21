FROM centos

RUN \
   yum -y install epel-release && \
   yum -y install git mongodb mongodb-server docker python-pip gcc python-devel python-devel openldap-devel && \
   pip install pymongo pytidylib docker-py sh web.py docutils simpleldap rpyc cgroup-utils && \
   mkdir -p /data/db

VOLUME /INGInious-local
VOLUME /sys/fs/cgroup
ADD init.sh /inginious-init.sh

WORKDIR /INGInious
CMD ["/inginious-init.sh"]
EXPOSE 80

RUN \
    git clone https://github.com/UCL-INGI/INGInious.git /INGInious && \
    ln -s /INGInious-local/configuration.json /INGInious/configuration.json && \
    ln -s /INGInious-local/configuration-agent.json /INGInious/configuration-agent.json
