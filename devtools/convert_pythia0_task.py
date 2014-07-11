# coding=utf-8
import json
import xmltodict
import sys
import os
import codecs
import html2text
import shutil
import  fnmatch
import re

os.mkdir("out")

def convertForMathJax(string):
    string = re.sub('< *img *[^>]* src=[\'"]http://latex.codecogs.com/svg.latex\?([^\'"]+)[\'"] [^>]*/*>','\\(\\1\\)',string)
    return string

for taskName in os.listdir("."):
    if not os.path.exists(taskName + "/task.desc"):
        continue
    
    # Open task.desc file
    file = codecs.open(taskName + "/task.desc", 'r', 'utf-8')
    content = file.read()
    task = xmltodict.parse(content, encoding='utf-8')['task']
    
    
    
    # Open constraints.desc
    for v in os.listdir(taskName+"/src"):
        const_file = taskName+"/src/"+ v + "/task.constraints"
        if not os.path.exists(const_file):
            continue
        file = open(const_file, 'r')
        content = file.read()
        const = xmltodict.parse(content)['task']
        
        # Update task
        ##############
        task['context'] = convertForMathJax(task['context'])
        task['contextIsHTML'] = True
        del task['level']
        task['name'] = task.pop('title')
        task['problems'] = task.pop('questions')
        
        if isinstance(task['problems']['question'], list):
            for item in task['problems']['question']:
                idd = item['@id']
                item['header'] = "<p class='lead'>"+convertForMathJax(item.pop('#text'))+"</p>"
                item['headerIsHTML'] = True
                item['type'] = item.pop('@type')
                
                if item['type'] == 'multiline':
                    item['type'] = 'code'
                elif item['type'] == 'line':
                    item['type'] = 'code-single-line'
                
                if '@header' in item:
                    item['header'] = item['header']+"<br/>"+convertForMathJax(item.pop('@header'))
                else:
                    item['header']= item['header']
                
                del item['@id']
                task['problems'][idd] = item
            del task['problems']['question']
        else:
            item = task['problems']['question']
            idd = item['@id']
            item['header'] = "<p class='lead'>"+convertForMathJax(item.pop('#text'))+"</p>"
            item['headerIsHTML'] = True
            item['type'] = item.pop('@type')
            
            if item['type'] == 'multiline':
                item['type'] = 'code'
            elif item['type'] == 'line':
                item['type'] = 'code-single-line'
            
            if '@header' in item:
                item['header'] = item['header']+"<br/>"+convertForMathJax(item.pop('@header'))
            else:
                item['header']= item['header']
            
            del item['@id']
            task['problems'][idd] = item
            del task['problems']['question']
            
        
        # Update constraints
        ####################
        if 'skeletons' in const:
            del const['skeletons']
            
        if 'questions' in const:
            const['problems'] = const.pop('questions')
        
            if isinstance(const['problems']['question'], list):
                for item in const['problems']['question']:
                    idd = item['@id']
                    if '@header' in item:
                        item['header'] = convertForMathJax(item.pop('@header'))
                    else:
                        item['header']= ''
                    item['headerIsHTML'] = True
                    
                    del item['@id']
                    const['problems'][idd] = item
                del const['problems']['question']
            else:
                item = const['problems']['question']
                idd = item['@id']
                if '@header' in item:
                    item['header'] = convertForMathJax(item.pop('@header'))
                else:
                    item['header'] = ' '
                item['headerIsHTML'] = True
                
                del item['@id']
                const['problems'][idd] = item
                del const['problems']['question']
        
            # Merge problems categories
            for item in task['problems']:
                if item in const['problems']:
                    header = task['problems'][item]["header"] + const['problems'][item]["header"]
                    task['problems'][item].update(const['problems'][item])
                    task['problems'][item]["header"] = header
            del const['problems']    
        
        # Adding limits to task
        ########################
        if 'constraints' in const:
            task['limits'] = const.pop('constraints')
            if 'maxtime' in task['limits']:
                task['limits']['time'] = int(task['limits'].pop('maxtime'))
            if 'maxmem' in task['limits']:
                task['limits']['memory'] = int(task['limits'].pop('maxmem'))
            task['limits']['disk'] = 50
            task['limits']['output'] = 5210
        
            if 'checkempty' in task['limits']:
                del task['limits']['checkempty']
            if 'language' in task['limits']:
                language = task['limits']['language']
            if 'submission' in task['limits']:
                del task['limits']['submission']
        task['environment']="pythia0compat"
        # Check problem types and generate multiple choices
        ###################################################
        
        #print json.dumps(task, sort_keys=True, indent=4, separators=(',', ': ')).encode('utf-8')
        
        for item in task['problems']:
            if item == '@nonumbered':
                del task['problems'][item]
                continue
            prob = task['problems'][item]
            if '@noexec' in prob:
                del prob['@noexec']
            if prob['type'] == 'multiplechoice':
                prob['type'] = 'multiple-choice'
                prob['choices'] = prob.pop('choice')
                prob['limit'] = int(prob.pop('@size'))
                i=0
                for it in prob['choices']:
                    prob['choices'][i]['text'] = prob['choices'][i].pop('#text')
                    prob['choices'][i]['textIsHTML'] = True
                    prob['choices'][i]['valid'] = json.loads(prob['choices'][i].pop('@valid'))
                    i += 1
                
            if '@single' in prob and prob['@single'] == 'single':
                del prob['@single']
            else:
                if '@single' in prob:
                    del prob['@single']
                prob['multiple'] = True
            
            if prob['type'] == "code":
                prob['language']= language
                
            task['problems'][item] = prob
            
        
        file = codecs.open("out/" + taskName + "_"+v+".task", "w", "utf-8")
        shutil.copytree(taskName+"/src/"+ v, "out/"+taskName + "_"+v)
        
        #Replace cp by cp -R in all files :D
        matches = []
        for root, dirnames, filenames in os.walk("out/"+taskName + "_"+v):
            for filename in fnmatch.filter(filenames, '*.sh'):
                matches.append(os.path.join(root, filename))
                
        for filepath in matches:
            print filepath
            filepath = filepath
            with codecs.open(filepath, 'r', 'utf-8') as file2:
                content = file2.read()

            content = re.sub("^cp[ \t]",'cp -R ', content, flags=re.IGNORECASE | re.MULTILINE)
            content = re.sub("[ \t]cp[ \t]",' cp -R ', content, flags=re.IGNORECASE | re.MULTILINE)  
            with codecs.open(filepath, 'w', 'utf-8') as file3:
                file3.write(content)
                
        file.write(json.dumps(task, indent=4, separators=(',', ': ')).encode('utf-8'))
        file.close()
