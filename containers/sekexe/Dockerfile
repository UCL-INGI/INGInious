FROM    inginious/default

ADD sekexe /sekexe

RUN yum -y install zsh
RUN mkdir /.__input
RUN mkdir /.__output
RUN mkdir /task
RUN mkdir /.__tests

CMD ["/sekexe/run", "/bin/INGInious"]
