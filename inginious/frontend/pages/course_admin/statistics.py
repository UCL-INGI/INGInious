# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Utilities for computation of statistics  """

def compute_statistics(tasks, data, ponderation):
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
            super_dict.setdefault(tag, {})
            super_dict[tag].setdefault(username, {})
            super_dict[tag][username].setdefault(submission["taskid"], [0,0,0,0])
            super_dict[tag][username][submission["taskid"]][0] += 1
            if "tests" in submission and tag.get_id() in submission["tests"] and submission["tests"][tag.get_id()]:
                super_dict[tag][username][submission["taskid"]][1] += 1

            if submission["best"]:
                super_dict[tag][username][submission["taskid"]][2] += 1
                if "tests" in submission and tag.get_id() in submission["tests"] and submission["tests"][tag.get_id()]:
                    super_dict[tag][username][submission["taskid"]][3] += 1

    output = []
    for tag in super_dict:

        if not ponderation: 
            results = [0,0,0,0]
            for username in super_dict[tag]:
                for task in super_dict[tag][username]:
                    for i in range (0,4):
                        results[i] += super_dict[tag][username][task][i] 
            output.append((tag, 100*safe_div(results[1],results[0]), 100*safe_div(results[3],results[2])))


        #Ponderation by stud and tasks
        else:
            results = ([], [])
            for username in super_dict[tag]:
                for task in super_dict[tag][username]:
                    a = super_dict[tag][username][task]
                    results[0].append(safe_div(a[1],a[0]))
                    results[1].append(safe_div(a[3],a[2]))
            output.append((tag, 100*safe_div(sum(results[0]),len(results[0])), 100*safe_div(sum(results[1]),len(results[1]))))

    return (fast_stats(data), output)

def fast_stats(data):
    """ Compute base statistics about submissions """
    
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
        (_("Evaluation submissions (Failed)"), total_submission_best - total_submission_best_succeeded),
        # add here new common statistics
        ]
    
    return statistics
    
def safe_div(x,y):
    """ Safe division to avoid /0 errors """
    if y == 0:
        return 0
    return x / y