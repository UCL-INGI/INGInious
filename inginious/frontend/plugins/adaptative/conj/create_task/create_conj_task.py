from distutils.dir_util import copy_tree
from string import Template

# copy subdirectory example
task_name = "jacques"
fromDirectory = "/home/naitali/Desktop/inginious/inginious_061018/INGInious/conj/create_task/task_template"
toDirectory = "/home/naitali/Desktop/inginious/inginious_061018/INGInious/conj/create_task/" + task_name

yaml_path = '/home/naitali/Desktop/inginious/inginious_061018/INGInious/conj/create_task/' + task_name + '/task.yaml'
js_path = '/home/naitali/Desktop/inginious/inginious_061018/INGInious/conj/create_task/' + task_name + '/public/input_random.js'

# d={ 'title':title, 'subtitle':subtitle, 'list':'\n'.join(list) }
d={ 'task_name': task_name}

copy_tree(fromDirectory, toDirectory)
task_yaml = open(yaml_path)
input_js = open(js_path)
#read it
yaml = Template(task_yaml.read())
js = Template(input_js.read())
#do the substitution
new_yaml = yaml.substitute(d)
new_js = js.substitute(d)

with open(yaml_path,'w') as f1:
    f1.write(new_yaml)
with open(js_path,'w') as f2:
    f2.write(new_js)
