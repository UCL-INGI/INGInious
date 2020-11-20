from inginious.frontend.task_dispensers import TaskDispenser


class TableOfContents(TaskDispenser):

    def __init__(self, course_tasks, dispenser_data):
        pass

    @classmethod
    def get_id(cls):
        return "toc"

    def render_edit(self):
        pass

    def render(self):
        pass

    def update_data(self):
        pass

    def is_task_accessible(self, username):
        pass

    def save_data(self):
        pass