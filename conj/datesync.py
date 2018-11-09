#!/usr/bin/env python3

import sys
import os
import json
import yaml

args = sys.argv

pathRepo = args[1]
path_file_date = args[2]
study_grp = args[3] #SINF or FSAB

json_data = open(path_file_date).read()

data = json.loads(json_data)
for i in range(0, int(data["nb_mission"])):
    elem = data["mission"][i]
    missionId = elem["id"]
    for dirname, subdirnames, subfilenames in os.walk(pathRepo):
        for subdirname in subdirnames:
            if (subdirname.startswith(missionId)):
                temp_value = ""
                if ("qcm" in subdirname):
                    temp_value = elem['date'][study_grp]['qcm']
                elif ("_bf" in subdirname):
                    temp_value = elem['date'][study_grp]['bf']
                elif ("real" in subdirname):
                    temp_value = elem['date'][study_grp]['mission']
                elif ("dem" in subdirname):
                    temp_value=elem['date'][study_grp]['dem']
                else:
                    temp_value=elem['date'][study_grp]['comp']
                stDoc = open(pathRepo +"/"+ subdirname + "/task.yaml",'r').read()
                f = yaml.load(stDoc)
                if temp_value=="" or not (temp_value):
                    pass
                else:
                    f["accessible"] = temp_value
                fa =open(pathRepo + "/" + subdirname + "/task.yaml", "w")
                fa.write(yaml.safe_dump(f, allow_unicode=True).encode().decode())
                fa.close()
