#!/bin/python3

import json

with open('/.__input/__inputdata.json', 'r') as thefile:
	data = json.load(thefile)
    
print(data.get("debug", False))