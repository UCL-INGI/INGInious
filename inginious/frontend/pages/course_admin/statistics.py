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
    total_submission = len(data)
    total_submission_best = 0
    total_submission_best_succeeded = 0
        
    for submission in data:
        if "best" in submission and submission["best"]:
            total_submission_best = total_submission_best + 1
            if "result" in submission and submission["result"] == "success":
                total_submission_best_succeeded += 1
        
    statistics = []
    statistics.append((_("Number of submissions"), total_submission))
    statistics.append((_("Evaluation submissions (Total)"), total_submission_best))
    statistics.append((_("Evaluation submissions (Succeeded)"), total_submission_best_succeeded))
    statistics.append((_("Evaluation submissions (Failed)"), total_submission_best - total_submission_best_succeeded))
    #Add here new common statistics
    
    
    tag_statistics = []
    for tag in task.get_tags():
        ok_total = 0
        ok_best = 0
        for submission in data:
            if "tests" in submission and tag.get_id() in submission["tests"] and submission["tests"][tag.get_id()]:
                ok_total += 1
            if "best" in submission and submission["best"] and "tests" in submission and tag.get_id() in submission["tests"] and submission["tests"][tag.get_id()]:
                ok_best += 1
        
        v_total = "0 %"
        v_best = "0 %"
        if total_submission != 0:
            v_total = str((int(ok_total/total_submission*100))) + " %"
        if total_submission_best != 0:
            v_best = str((int(ok_best/total_submission_best*100))) + " %"
        tag_statistics.append((tag, v_total, v_best))
        
    return (statistics, tag_statistics)


