# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Utilities for computation of statistics  """

def compute_statistics(task, data):
    """ 
    Compute statistics about submissions and tags.
    This function returns a tuple of lists following the format describe below:
    (   
        [('Number of submissions', 13), ('Evaluation submissions', 2), …], 
        [(<tag>, '61%', '50%'), (<tag>, '76%', '100%'), …]
    )
     """
     
    has_sumbissions = False
    for submission in data:
        if submission["taskid"] == task.get_id():
            has_sumbissions = True
            break
    if has_sumbissions == False:
        return (None, None)

    total_submission = 0
    total_submission_best = 0
    total_submission_best_succeeded = 0
        
    for submission in data:
        if submission["taskid"] == task.get_id():
            total_submission += 1
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
    
    tag_statistics = []
    for tag in task.get_tags()[0] + task.get_tags()[1]:
        ok_total = 0
        ok_best = 0
        for submission in data:
            if submission["taskid"] == task.get_id():
                if "tests" in submission and tag.get_id() in submission["tests"] and submission["tests"][tag.get_id()]:
                    ok_total += 1
                if "best" in submission and submission["best"] and "tests" in submission and tag.get_id() in submission["tests"] and submission["tests"][tag.get_id()]:
                    ok_best += 1
        
        v_total = 0
        v_best = 0
        if total_submission != 0:
            v_total = int(ok_total/total_submission*100)
        if total_submission_best != 0:
            v_best = int(ok_best/total_submission_best*100)
        tag_statistics.append((tag, v_total, v_best))

    return (statistics, tag_statistics)

def fusion_statistics(tasks, data):

    all_statistics = []
    all_tag_statistics = []
    
    for task in tasks:
        (statistics, tag_statistics) = compute_statistics(task, data)
        if statistics != None:
            all_statistics.append(statistics)
        if tag_statistics != None:
            all_tag_statistics.append(tag_statistics)
       
    #Merge tuples
    dict_stat = {}
    for l in all_statistics:
        for i in range(len(l)):
            if l[i][0] not in dict_stat:
                dict_stat[l[i][0]] = 0
            dict_stat[l[i][0]] += l[i][1]
    statistics = [(k, v) for k, v in dict_stat.items()]

    dict_tag = {}
    for l in all_tag_statistics:
        for t in l: #For each tuples (<tag>, 0, 0)
            if t != []:
                if t[0] not in dict_tag:
                    dict_tag[t[0]] = [0, 0, 0]
                dict_tag[t[0]][0] += t[1]
                dict_tag[t[0]][1] += t[2]
                dict_tag[t[0]][2] += 1
    tag_statistics = [(k, v[0]/v[2], v[1]/v[2]) for k, v in dict_tag.items()]

    return(statistics, tag_statistics)