import json
import sys

input = json.loads(sys.stdin.readline())
print json.dumps({"result":"failed","text":"In fact, it's working, but it's a test :D","problems":input})