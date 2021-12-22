import unittest
from genmihatests import *

class unit_test(unittest.TestCase):

    def test_char_counter(self):
    
        self.assertEqual(char_counter('Bogomolov','o'), 4)
        
    
    def test_factorial(self):
        
        self.assertEqual(factorial(6), 720)
        
        
    def test_fibonachi(self):
    
        self.assertEqual(fibonachi(7), 13)
        

if '__name__'=='__main__':
    unittest.main()
    
    
    
