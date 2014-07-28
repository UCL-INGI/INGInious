import unittest
import common.base
import common.tasks
import common.courses
import common.tasks_code_boxes
from tests import *

class common_tasks_basic(unittest.TestCase):
    def setUp(self):
        print "\033[1m-> common_tasks_basic:setUp_:begin\033[0m"
    
    def test_task_loading(self):
        '''Tests if a course file loads correctly'''
        t = common.tasks.Task(common.courses.Course('test'), 'task1')
        assert t.get_environment() == 'default'
        assert t.get_id() == 'task1'
        assert t.get_course_id() == 'test'
        assert t.get_response_type() == 'rst'
        
        lim = t.get_limits()
        assert lim['disk'] == 100
        assert lim['memory'] == 32
        assert lim['time'] == 60
        
        assert t.get_problems()[0].get_type() == 'code'
    
    def tearDown(self):
        print "\033[1m-> common_tasks_basic:setUp_:tearDown\033[0m"

class common_tasks_problems(unittest.TestCase):
    def setUp(self):
        print "\033[1m-> common_tasks_problems:setUp_:begin\033[0m"
    
    def test_problem_types(self):
        '''Tests if problem types are correctly recognized'''
        t = common.tasks.Task(common.courses.Course('test2'), 'task1')
        assert t.get_problems()[0].get_type() == 'match'
        
        t = common.tasks.Task(common.courses.Course('test2'), 'task2')
        assert t.get_problems()[0].get_type() == 'match'
        
        t = common.tasks.Task(common.courses.Course('test2'), 'task3')
        assert t.get_problems()[0].get_type() == 'multiple-choice'
    
    def test_multiple_choice(self):
        '''Tests multiple choice problems methods'''
        p = common.tasks.Task(common.courses.Course('test2'), 'task3').get_problems()[0]
        assert p.allow_multiple()
        
        # Check correct and incorrect answer
        assert p.check_answer({'unittest':[0,1]})[0]
        assert not p.check_answer({'unittest':[0,1,2]})[0]
        
        # Check random form input
        assert p.input_is_consistent({'unittest':[0,1]})
        assert not p.input_is_consistent('test')
        assert not p.input_is_consistent((10, 42))
    
    def test_match(self):
        '''Tests match problems methods'''
        p = common.tasks.Task(common.courses.Course('test2'), 'task1').get_problems()[0]
        
        # Check correct and incorrect answer
        assert p.check_answer({'unittest':'Answer 1'})[0]
        assert not p.check_answer({'unittest':'Wrong answer'})[0]
        
        # Check random form input
        assert p.input_is_consistent({'unittest':'Answer'})
        assert not p.input_is_consistent('test')
        assert not p.input_is_consistent((10, 42))
    
    def test_code(self):
        '''Tests code problems methods'''
        p = common.tasks.Task(common.courses.Course('test'), 'task1').get_problems()[0]
        
        # Check random form input
        assert p.input_is_consistent({'unittest/decimal':'10'})
        assert not p.input_is_consistent('test')
        assert not p.input_is_consistent({'unittest':'10'})
        
    def tearDown(self):
        print "\033[1m-> common_tasks_problems:setUp_:tearDown\033[0m"

class common_tasks_boxes(unittest.TestCase):
    def setUp(self):
        print "\033[1m-> common_tasks_boxes:setUp_:begin\033[0m"
    
    def test_number_boxes(self):
        '''Tests if get_boxes returns the correct number of boxes'''
        p = common.tasks.Task(common.courses.Course('test2'), 'task4').get_problems()[0]
        assert len(p.get_boxes()) == 12
    
    def test_filebox(self):
        '''Tests filebox methods'''
        p = common.tasks.Task(common.courses.Course('test2'), 'task4').get_problems()[0]
        box = p.get_boxes()[11]
        assert box.get_type() == 'file'
        
        # Check random form input
        assert box.input_is_consistent({"unittest/file1": {"filename":"test.txt", "value":"test"}})
        assert not box.input_is_consistent({"unittest/file1": {"filename":"test.txt", "content":"test"}})
        assert not box.input_is_consistent("test")
    
    def test_integer_inputbox(self):
        '''Tests integer inputbox methods'''
        p = common.tasks.Task(common.courses.Course('test2'), 'task4').get_problems()[0]
        box = p.get_boxes()[1]
        assert box.get_type() == 'input' and box._input_type =='integer'
        
        # Check random form input
        assert box.input_is_consistent({"unittest/int1": "42"})
        assert not box.input_is_consistent({"unittest/int1": "test"})
        assert not box.input_is_consistent("ddd")
        assert not box.input_is_consistent(42)
    
    def test_decimal_inputbox(self):
        '''Tests decimal inputbox methods'''
        p = common.tasks.Task(common.courses.Course('test2'), 'task4').get_problems()[0]
        box = p.get_boxes()[3]
        assert box.get_type() == 'input' and box._input_type =='decimal'
        
        # Check random form input
        assert box.input_is_consistent({"unittest/decimal1": "42.3"})
        assert not box.input_is_consistent({"unittest/decimal1": "test"})
        assert not box.input_is_consistent("ddd")
        assert not box.input_is_consistent(42)
    
    def test_text_inputbox(self):
        '''Tests text inputbox methods'''
        p = common.tasks.Task(common.courses.Course('test2'), 'task4').get_problems()[0]
        box = p.get_boxes()[5]
        assert box.get_type() == 'input' and box._input_type =='text'
        
        # Check random form input
        assert box.input_is_consistent({"unittest/text1": "42.3"})
        assert box.input_is_consistent({"unittest/text1": "test"})
        assert not box.input_is_consistent("ddd")
        assert not box.input_is_consistent(42)
    
    def test_multiline_inputbox(self):
        '''Tests multiline inputbox methods'''
        p = common.tasks.Task(common.courses.Course('test2'), 'task4').get_problems()[0]
        box = p.get_boxes()[8]
        assert box.get_type() == 'multiline'
        
        # Check random form input
        assert box.input_is_consistent({"unittest/code1": "42.3"})
        assert box.input_is_consistent({"unittest/code1": "test"})
        assert not box.input_is_consistent("ddd")
        assert not box.input_is_consistent(42)
        
    def tearDown(self):
        print "\033[1m-> common_tasks_boxes:setUp_:tearDown\033[0m"

if __name__ == "__main__":
    unittest.main()
