#! /bin/bash
if ! boot2docker ip > /dev/null 2> /dev/null
then boot2docker up
fi

if boot2docker ssh test -e /inginious/agent.installed
then echo "Agent dependencies already installed, skipping installation."
else
    boot2docker ssh sudo tce-load -wi python-distribute python-dev openssl-1.0.0 compiletc
    boot2docker ssh sudo easy_install pip
    boot2docker ssh sudo pip install docker-py rpyc cgroup-utils docutils
    boot2docker ssh sudo mkdir /inginious
    boot2docker ssh sudo touch /inginious/agent.installed
    docker pull ingi/inginious-c-default
fi

cd "$( dirname "${BASH_SOURCE[0]}" )"
cd ../..
dir=$(pwd)
ip=$(boot2docker ip)
echo "I will now start the agent. The IP to indicate in configuration.json is $ip"
echo ""
echo ""

boot2docker ssh -t "cd $dir && sudo python app_agent.py"
