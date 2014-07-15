import threading
import json
from abc import ABCMeta, abstractmethod
from common.parsableText import ParsableText

class JobManager (threading.Thread):
    """ Abstract thread class that runs the jobs that are in the queue """
    __metaclass__ = ABCMeta
    
    def __init__(self,queue):
        threading.Thread.__init__(self)
        self.queue = queue
        
    def run(self):
        while True:
            # Retrieves the task from the queue
            jobId,task,inputdata,callback = self.queue.getNextJob()
            
            # Base dictonnary with output
            basedict = {"task":task,"input":inputdata}
            
            # Check task answer that do not need emulation
            first_result,need_emul,first_text,first_problems = task.checkAnswer(inputdata)
            finaldict = basedict.copy()
            finaldict.update({"result": ("success" if first_result else "failed")})
            if first_text != None:
                finaldict["text"] = first_text
            if first_problems:
                finaldict["problems"] = first_problems
            
            # Launch the emulation
            if need_emul:
                try:
                    emul_result = self.runJob(jobId, task, {"limits": task.getLimits(), "input": inputdata})
                    print json.dumps(emul_result, sort_keys=True, indent=4, separators=(',', ': '))
                except Exception:
                    emul_result = {"result":"error","text":"The grader did not gave any output. This can be because you used too much memory."}
                
                if finaldict['result'] not in ["error","failed","success","timeout","overflow"]:
                    finaldict['result'] = "error"
                    
                if emul_result["result"] not in ["error","timeout","overflow"]:
                    # Merge results
                    novmDict = finaldict
                    finaldict = emul_result
                    
                    finaldict["result"] = "success" if novmDict["result"] == "success" and finaldict["result"] == "success" else "failed"
                    if "text" in finaldict and "text" in novmDict:
                        finaldict["text"] = finaldict["text"]+"\n"+"\n".join(novmDict["text"])
                    elif "text" not in finaldict and "text" in novmDict:
                        finaldict["text"] = "\n".join(novmDict["text"])
                    
                    if "problems" in finaldict and "problems" in novmDict:
                        for p in novmDict["problems"]:
                            if p in finaldict["problems"]:
                                finaldict["problems"][p] = finaldict["problems"][p] + "\n" + novmDict["problems"][p]
                            else:
                                finaldict["problems"][p] = novmDict["problems"][p]
                    elif "problems" not in finaldict and "problems" in novmDict:
                        finaldict["problems"] = novmDict["problems"]
                elif emul_result["result"] in ["error","timeout","overflow"] and "text" in emul_result:
                    finaldict = basedict.copy()
                    finaldict.update({"result":emul_result["result"],"text":emul_result["text"]})
                elif emul_result["result"] == "error":
                    finaldict = basedict.copy()
                    finaldict.update({"result":emul_result["result"],"text":"An unknown internal error occured"})
                elif emul_result["result"] == "timeout":
                    finaldict = basedict.copy()
                    finaldict.update({"result":emul_result["result"],"text":"Your code took too much time to execute"})
                elif emul_result["result"] == "overflow":
                    finaldict = basedict.copy()
                    finaldict.update({"result":emul_result["result"],"text":"Your code took too much memory or disk"})
            
            # Parse returned content
            if "text" in finaldict:
                finaldict["text"] = ParsableText(finaldict["text"],task.getResponseType()).parse()
            if "problems" in finaldict:
                for pid in finaldict["problems"]:
                    finaldict["problems"][pid] = ParsableText(finaldict["problems"][pid],task.getResponseType()).parse()
                    
            self.queue.setResult(jobId, finaldict)
            if callback != None:
                callback(jobId, finaldict)
                
    @abstractmethod
    def runJob(self, jobId, task, inputdata):
        pass