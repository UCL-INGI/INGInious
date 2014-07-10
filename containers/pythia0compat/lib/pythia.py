# -*- coding: utf-8 -*-
# Pythia library for writing tasks and feedback scripts
# Author: Sébastien Combéfis <sebastien@combefis.be>
# Copyright (C) 2012, Université catholique de Louvain
# Copyright (C) 2012, Computer Science and IT in Education ASBL
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, os, re, xml.dom.minidom, csv

def clean(str):
    str = str.replace('&', '&#38;')
    str = str.replace('>', '&#62;')
    str = str.replace('<', '&#60;')
    str = str.replace('"', '&#34;')
    return str

class NoAnswerException(Exception):
    
    '''Exception representing the case where no answer was provided'''
    
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class UndeclaredException(Exception):
    
    '''Exception representing the case where a variable has not been declared'''
    
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class TestSuite:
    
    '''Basic test suite'''
    
    def __init__(self, id, predefined = []):
        self.id = id
        self.predefined = predefined
    
    def check(self, data):
        try:
            answer = self.studentCode(data)
        except NoAnswerException as e:
            return e.value
        except UndeclaredException as e:
            return e.value
        except Exception as e:
            return 'exception:{}'.format(e)
        res = self.moreCheck(answer, data)
        if res != 'passed':
            return res
        return 'checked:{}'.format(answer)
    
    def studentCode(self, data):
        return None
    
    def moreCheck(self, answer, data):
        return 'passed'
    
    def parseTestdata(self, data):
        return tuple(data)
    
    def run(self):
        resfile = open('output/{}.res'.format(self.id), 'w', encoding = 'utf-8')
        
        # Predefined tests
        for data in self.predefined:
            res = self.check(data)
            resfile.write('{}\n'.format(res))
        
        # Random tests
        testpath = 'input/{}.csv'.format(self.id)
        if os.path.exists(testpath):
            file = open(testpath, 'r', encoding = 'utf-8')
            reader = csv.reader(file, delimiter=';', quotechar='"')
            for row in reader:
                res = self.check(self.parseTestdata(row))
                resfile.write('{}\n'.format(res))
            file.close()
        
        resfile.close()


class FeedbackMessage():
    
    '''Class for messages generated in the feedbacks'''
    
    def timeexceeded(self):
        return '<p>Your program took too much time to execute and exceeded the time limit.</p>'
    
    def generalerror(self):
        return '<p>An error occured while executing your code.</p>'
    
    def compileerror(self, msg):
        return '<p>Compile-time error (your program is thus badly written) :</p><pre>{}</pre>'.format(clean(msg))
    
    def correct(self):
        return '<p>Your answer is correct.</p>'
    
    def noanswer(self):
        return '<p>You did not answer the question.</p>'
    
    def exception(self, msg):
        return '<p>Your code produced an exception (error while executing).</p><pre>{}</pre>'.format(clean(msg))
    
    def undeclared(self, var):
        return '<p>You have not declared a <b>&#171;&#160;{}&#160;&#187;</b> variable.</p>'.format(var)
    
    def badtype(self, type):
        return '<p>Your answer must be {}.</p>'.format(type)
    
    def badvalue(self, var, val, paramslist = None, paramsval = None, expected = None):
        header = '<p>You have not initialised the <b>&#171;&#160;' + var + '&#160;&#187;</b> variable with the right value.'
        if paramslist == None and paramsval == None and expected == None:
            return header + ' It indeed contains the value ' + val +  '.</p>'
        params = '<b>&#171;&#160;' + paramslist[0] + '&#160;&#187;</b> is ' + paramsval[0]
        for i in range(1, len(paramslist)):
            params += (', ' if i < len(paramslist) - 1 else ' and ') + '<b>&#171;&#160;' + paramslist[i] + '&#160;&#187;</b> is ' + paramsval[i]
        return header + ' For example, if ' + params + ', you return ' + result + ' instead of ' + expected + '.</p>'
    
    def unchanged(self, var, val, paramslist = None, paramsval = None, expected = None):
        header = '<p>You have not updated the <b>&#171;&#160;' + var + '&#160;&#187;</b> variable with the right value.'
        if paramslist == None and paramsval == None and expected == None:
            return header + ' It indeed contains the value ' + val + '.</p>'
        params = '<b>&#171;&#160;' + paramslist[0] + '&#160;&#187;</b> is ' + paramsval[0]
       	for i in range(1, len(paramslist)):
            params += (', ' if i < len(paramslist) - 1 else ' and ') + '<b>&#171;&#160;' + paramslist[i] + '&#160;&#187;</b> is ' + paramsval[i]
        return header + ' For example, if ' + params + ', its value is ' + val + ' instead of ' + expected + '.</p>'
    
    def default(self, code):
        return '<p>Incorrect answer ({}).</p>'.format(clean(msg).encode())


class Feedback:
    
    '''Generic class for generating a feedback for a problem'''
    
    def __init__(self, fbks, feedbackMsg = FeedbackMessage()):
        self.fbks = fbks
        self.feedbackMsg = feedbackMsg
        self.status = -1
        self.exitcode = -1
        
        # Checking status file
        statuspath = 'output/status'
        if os.path.exists(statuspath):
            with open(statuspath, encoding = 'utf-8') as file:
                self.status = file.readline()
        
        # Checking exitcode file
        exitcodepath = 'output/exitcode'
        if os.path.exists(exitcodepath):
            with open(exitcodepath, encoding = 'utf-8') as file:
                try:
                    self.exitcode = int(file.readline().strip())
                except ValueError:
                    pass
    
    def _generalFeedback(self, msg):
        return '<feedback><general><![CDATA[{}]]></general><verdict>KO</verdict></feedback>'.format(msg)
    
    def generate(self):
        # Check the general status of the execution
        if self.status != 'done':
            errormsg = self.feedbackMsg.generalerror()
            if self.status == 'timeout':
                errormsg = self.feedbackMsg.timeexceeded()
            with open('feedback.xml', 'w', encoding = 'utf-8') as file:
                file.write(self._generalFeedback(errormsg))
            return
        
        # Check general error of the execution
        errpath = 'output/stderr'
        if os.path.exists(errpath):
            with open(errpath, encoding = 'utf-8') as file:
                errormsg = file.read()
            if errormsg != '':
                with open('feedback.xml', 'w', encoding = 'utf-8') as file:
                    file.write(self._generalFeedback('<p>Une erreur s\'est produite pendant la correction de votre soumission.</p><pre>{}</pre>'.format(clean(errormsg))))
                return
        
        # Check every question
        problemSucceeded = True
        output = ''
        for feedback in self.fbks:
            (verdict, content) = feedback.correct()
            problemSucceeded = problemSucceeded and verdict == 'OK'
            output += content
        
        # Writing feedback to file
        with open('feedback.xml', 'w', encoding = 'utf-8') as file:
            file.write('<feedback>{}<verdict>{}</verdict></feedback>'.format(output, 'OK' if problemSucceeded else 'KO'))


class FeedbackSuite:

    '''Basic feedback suite'''

    def __init__(self, id, predefined = [], feedbackMsg = FeedbackMessage()):
        self.id = id
        self.predefined = predefined
        self.feedbackMsg = feedbackMsg
    
    def _generateOutput(self, verdict, msg):
        return (verdict, '<question id="{}" verdict="{}"><![CDATA[{}]]></question>'.format(self.id, verdict, msg))

    def correct(self):
        # Checking execution error, if any
        errpath = 'output/files/{}.err'.format(self.id)
        if os.path.exists(errpath):
            with open(errpath, 'r', encoding = 'utf-8') as file:
                error = file.read()
                if error != '':
                    return self._generateOutput('KO', self.feedbackMsg.compileerror(error))
        
        # Checking standard output, if any
        outpath = 'output/files/{}.out'.format(self.id)
        if os.path.exists(outpath):
            with open(outpath, 'r', encoding = 'utf-8') as file:
                out = file.read()
                (msg, verdict) = self.checkStdout(self.id, out)
                if verdict != 'none':
                    return self._generateOutput(verdict, msg)
        
        # Checking test dataset results, if any
        respath = 'output/files/{}.res'.format(self.id)
        if os.path.exists(respath):
            with open(respath, 'r', encoding = 'utf-8') as resfile:
                # Check predefined test
                for input in self.predefined:
                    value = resfile.readline().strip()
                    tokens = value.split(':')
                    if tokens[0] == 'checked':
                        expected = self.teacherCode(*input)
                        value = self.parseAnswer(tokens[1])
                        if value != expected:
                            return self._generateOutput('KO', self.badvalue(input, value, expected))
                    else:
                        return self._generateOutput('KO', self.checkReturn(self.id, value))
                # Check generated tests sets
                testpath = 'input/{}.csv'.format(self.id)
                if os.path.exists(testpath):
                    with open(testpath, 'r', encoding = 'utf-8') as infile:
                        inreader = csv.reader(infile, delimiter=';', quotechar='"')
                        for row in inreader:
                            value = resfile.readline().strip()
                            tokens = value.split(':')
                            if tokens[0] == 'checked':
                                args = self.parseTestdata(row)
                                expected = self.teacherCode(*args)
                                value = self.parseAnswer(tokens[1])
                                if value != expected:
                                    return self._generateOutput('KO', self.badvalue(args, value, expected))
                            else:
                                return self._generateOutput('KO', self.checkReturn(self.id, value))
        
        return self._generateOutput('OK', '')

    def checkStdout(self, qid, out):
        return ('', 'none')

    def checkReturn(self, qid, out):
        return ''

    def parseTestdata(self, data):
        return tuple(data)
    
    def parseAnswer(self, answer):
        return str(answer.strip())

    def teacherCode(self, data):
        return None

    def badvalue(self, args, value, exp):
        return None


class BasicFeedbackSuite (FeedbackSuite):
    
    def __init__(self, id, predefined = [], feedbackMsg = FeedbackMessage()):
        FeedbackSuite.__init__(self, id, predefined, feedbackMsg)
    
    def checkReturn(self, qid, out):
        code = out.split(':')
        if code[0] == 'exception':
            return self.feedbackMsg.exception(code[1])
        elif code[0] == 'no_answer':
            return self.feedbackMsg.noanswer()
        else:
            return 'passed'


class TestDataSet:

    '''Basic test generator'''

    def __init__(self, qid, size):
        self.qid = qid
        self.size = size
    
    def generate(self):
        with open('input/' + str(self.qid) + '.csv', 'w', encoding = 'utf-8') as file:
            writer = csv.writer(file, delimiter=';', quotechar='"')
            for i in range(self.size):
                writer.writerow(self.genTestData())
    
    def genTestData(self):
        return []
