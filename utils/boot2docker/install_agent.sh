#! /bin/bash
tce-load -wi python-distribute python-dev openssl-1.0.0 compiletc
sudo easy_install pip
sudo pip install docker-py rpyc cgroup-utils docutils