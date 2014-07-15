# DOCKER-VERSION 1.1.0

FROM    inginious/default

# Install Oz
ADD     . /mozartRPM
RUN     rpm -i /mozartRPM/mozart2-2.0.0-3777-x86_64.rpm

# Environment variables
RUN     echo "export OZHOME=/opt/mozart2" >> /etc/profile.d/oz.sh
RUN     echo "export PATH=/opt/mozart2/bin:$""PATH" >> /etc/profile.d/oz.sh

# Making symbolic links
RUN     ln /opt/mozart2/bin/oz /bin/oz
RUN     ln /opt/mozart2/bin/ozc /bin/ozc
RUN     ln /opt/mozart2/bin/ozemulator /bin/ozemulator
RUN     ln /opt/mozart2/bin/ozemulator_bin /bin/ozemulator_bin
RUN     ln /opt/mozart2/bin/ozengine /bin/ozengine
RUN     ln /opt/mozart2/bin/ozwish /bin/ozwish
RUN     ln /opt/mozart2/bin/ozwish_bin /bin/ozwish_bin
