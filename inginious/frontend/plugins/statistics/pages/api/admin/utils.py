def project_detail_user_tasks(user_tasks):
    return [{
        "grade": s["grade"],
        "username": s["username"],
        "submission": project_submission(s.get("submission", None))
    } for s in user_tasks]

def task_submissions_detail(submissions):
    return [{
        "grade": s["grade"],
        "username": s["username"],
        "id": str(s["_id"]),
        "status": s["status"],
        "submitted_on": str(s["submitted_on"]),
        "summary_result": s["custom"]["summary_result"]

    } for s in submissions]

def project_submission(submission):
    if submission is None:
        return None

    return {
        "id": str(submission["_id"]),
        "submitted_on": submission["submitted_on"].isoformat(),
        "taskId": submission["taskid"],
        "status": submission["status"],
        "result": submission["result"],
        "grade": submission["grade"],
        "summary_result": submission.get("custom", {}).get("summary_result", None)
    }
