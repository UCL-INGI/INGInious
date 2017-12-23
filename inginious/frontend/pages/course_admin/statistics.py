# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Utilities for computation of statistics  """

def compute_statistics(tasks, data, ponderation=3):
    """ 
    Compute statistics about submissions and tags.
    This function returns a tuple of lists following the format describe below:
    (   
        [('Number of submissions', 13), ('Evaluation submissions', 2), …], 
        [(<tag>, '61%', '50%'), (<tag>, '76%', '100%'), …]
    )
     """
    
    super_dict = {}
    for submission in data:
        task = tasks[submission["taskid"]]
        username = "".join(submission["username"])
        tags_of_task = task.get_tags()[0] + task.get_tags()[1]
        for tag in tags_of_task:
            if tag not in super_dict:
                super_dict[tag] = {}
            if username not in super_dict[tag]:
                super_dict[tag][username] = {}
            if submission["taskid"] not in super_dict[tag][username]:
                super_dict[tag][username][submission["taskid"]] = [0,0,0,0]
            super_dict[tag][username][submission["taskid"]][0] += 1
            if tag.get_id() in submission["tests"] and submission["tests"][tag.get_id()] == True:
                super_dict[tag][username][submission["taskid"]][1] += 1
                    
            if (submission["best"] == True):
                super_dict[tag][username][submission["taskid"]][2] += 1
                if tag.get_id() in submission["tests"] and submission["tests"][tag.get_id()] == True:
                    super_dict[tag][username][submission["taskid"]][3] += 1
    
    output = []
    for tag in super_dict:
        if ponderation == 0: #No ponderation
            results = [0,0,0,0]
            for username in super_dict[tag]:
                for task in super_dict[tag][username]:
                    results[0] += super_dict[tag][username][task][0] 
                    results[1] += super_dict[tag][username][task][1] 
                    results[2] += super_dict[tag][username][task][2] 
                    results[3] += super_dict[tag][username][task][3]
            output.append((tag, 100*results[1]/results[0] if results[0] != 0 else 0, 100*results[3]/results[2] if results[2] != 0 else 0))
        
        if ponderation == 3: #Ponderation by stud and tasks
            results = ([], [])
            for username in super_dict[tag]:
                for task in super_dict[tag][username]:
                    results[0].append(super_dict[tag][username][task][1]/super_dict[tag][username][task][0] if super_dict[tag][username][task][0] != 0 else 0)
                    results[1].append(super_dict[tag][username][task][3]/super_dict[tag][username][task][2] if super_dict[tag][username][task][2] != 0 else 0)
            output.append((tag, 100*sum(results[0])/len(results[0]) if len(results[0]) != 0 else 0, 100*sum(results[1])/len(results[1]) if len(results[1]) != 0 else 0))

    return (fast_stats(data), output)
    
def fast_stats(data):
    total_submission = len(data)
    total_submission_best = 0
    total_submission_best_succeeded = 0
        
    for submission in data:
        if "best" in submission and submission["best"]:
            total_submission_best = total_submission_best + 1
            if "result" in submission and submission["result"] == "success":
                total_submission_best_succeeded += 1
        
    statistics = [
        (_("Number of submissions"), total_submission),
        (_("Evaluation submissions (Total)"), total_submission_best),
        (_("Evaluation submissions (Succeeded)"), total_submission_best_succeeded),
        (_("Evaluation submissions (Failed)"), total_submission_best - total_submission_best_succeeded)
        # add here new common statistics
        ]
    
    return statistics