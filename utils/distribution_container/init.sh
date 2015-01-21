#! /bin/bash
mongod &
/INGInious/app_agent.py &
/INGInious/app_frontend.py 80
