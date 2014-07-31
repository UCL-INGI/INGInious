# -*- coding: utf-8 -*-
# Feedback script
# Author: Sébastien Combéfis
# Date: November 09, 2012
# Modified by: Adrien Bibal
# Modification date: 2013-2014
# Problem: HelloWorld

import compil_check
import running_check
import codecs
import cgi

error = 0 # init: 0 = no error

# If there is a compilation error, this method is called.
# msg is the compilation error message.
def compileerror(msg):
    global error
    error = 1 # init: 1 = compilation error
    # mapLines is used to map the error line in the error message to the problematic line in the student code.
    # For instance, if the second line in the student answer is problematic, it will point out the line 2.
    # (and not the number of the line in the entire file, with the lines wrote by the TA)
    new_msg = mapLines("proc {PrintHello}", msg) # The first argument is the "line 0" marker. 

    file_path = "new_file.oz"

    error_message = "There is a compilation error!\n"

    # All the checks in compil_check are run.
    error_message += compil_check.checkLowercaseVar(file_path)
    error_message += compil_check.checkDeclare(file_path)
    error_message += compil_check.checkNotIntroduced(msg)
    error_message += compil_check.checkCallWithAtom(msg)
    error_message += compil_check.checkIllegalArity(msg)
    error_message += compil_check.checkIllegalUseOfNesting(msg)
    error_message += compil_check.checkParseError(msg)
    error_message += compil_check.checkEqualityConstraint(msg)
    error_message += compil_check.checkExpressionStatement(msg)

    # Write the error message given by the compiler.
    error_message += 'The error given by the compiler is:\n {}'.format("</p><pre>"+new_msg+"</pre>")
    # Trick so students don't know the name of the file so easily.
    error_message = error_message.replace("new_file.oz", "exercise.oz")
    # Delete this useless line (for our purpose) in the error message.
    error_message = error_message.replace("Mozart Compiler 2.0.0-alpha.0+build.3777.62f3ec5 (Fri, 23 Aug 2013 23:51:55 -0700) playing Oz 3\n", "")

    # Create and print the JSON with the message "error_message" and 'KO' status
    JSON(error_message, 'KO')

# If there is a runtime error, this method is called.
# msg is the runtime error message.
def runningerror(msg):
    global error
    error = 2 # init: 2 = runtime error
    # mapLines is used to map the error line in the error message to the problematic line in the student code.
    # For instance, if the second line in the student answer is problematic, it will point out the line 2.
    # (and not the number of the line in the entire file, with the lines wrote by the TA)
    new_msg = mapLines("proc {PrintHello}", msg) # The first argument is the "line 0" marker.
    error_message = 'There is a runtime error! '

    # All the checks in running_check are run.
    error_message += running_check.checkMissingElseClause(msg)
    error_message += running_check.checkIllegalFieldSelection(msg)
    error_message += running_check.checkMaximalHeapSize(msg)
    error_message += running_check.checkCPUTimeLimit(msg)

    # Write the error message given by the emulator.
    error_message += 'The error given by the emulator is:\n {}'.format("</p><pre>"+new_msg+"</pre>")
    # Trick so students don't know the name of the file so easily.
    error_message = error_message.replace("new_file.oz", "exercise.oz")
    # Delete this useless line (for our purpose) in the error message.
    error_message = error_message.replace("Mozart Compiler 2.0.0-alpha.0+build.3777.62f3ec5 (Fri, 23 Aug 2013 23:51:55 -0700) playing Oz 3\n", "")

    # Create and print the JSON with the message "error_message" and 'KO' status
    JSON(error_message, 'KO')

# Change the line number in the error file so that it corresponds to the number of line in the student answer.
# fun_name is the marker of "line 0" in new_file.oz
# err_msg is the error message.
def mapLines(fun_name, err_msg):
    file_path = "new_file.oz"
    oz_file = open(file_path)
    count = 0
    # Count the number of lines to reach the marker.
    for line in oz_file:
        count += 1
        if fun_name in line:
            count += 1
            break
    oz_file.close()

    new_line = ""
    err_file = err_msg
    # For each line in the error message
    for line in err_file.split("\n"):
        # If the line contains the number to change, change it to num_line - count + 1.
        if "in file \"new_file.oz\"" in line:
            position = line.find(" line ")
            position = position + 6 # To go after these chars: " line "
            num_line = ""
            length_num = 0
            for char in line[position:]:
                if char == " " or char == ",":
                    break
                length_num += 1
                num_line += char
            num_line = int(num_line)
            num_line = num_line - count + 1 # Change the line number
            new_line += line[:position] + " " + str(num_line) + line[position+length_num:] + "\n"
        # Else, just write the line.
        else:
            new_line += line + "\n"

    return new_line

# This method takes the message and the status to return to the frontend and print the JSON containing these info.
def JSON(message, status):
    global error
    correct = "true"
    score = "1"
    if status == "KO":
        correct = "false"
        score = "0"
    if error == 0:
        message = cgi.escape(message).replace("\"", "&#34;").replace("\n","<br />").replace("%","&#37;") # Transformation for html.
        if status == "OK":
            print("{\"correct\": "+correct+", \"score\": "+score+", \"msg\": \"<p>"+message+"</p>\"}", end='')
        else:
            splitted = message.split("Your answer: ")
            message = "<ul><li><i>"+"Your answer: "+"</i>"+splitted[1].split("Expected answer: ")[0]+"</li>Expected answer: "+splitted[1].split("Expected answer: ")[1]
            splitted = message.split("Expected answer: ")
            if "&lt;&#37;&#37;&#37;&#37;&#37;&gt;" in message:
                message = splitted[0]+"<li><i>"+"Expected answer: "+"</i>"+splitted[1].split("&lt;&#37;&#37;&#37;&#37;&#37;&gt;")[0]+"</li></ul>"+"<p>"+splitted[1].split("&lt;&#37;&#37;&#37;&#37;&#37;&gt;")[1]+"</p>"
            else:
                message = splitted[0]+"<li><i>"+"Expected answer: "+"</i>"+splitted[1]+"</li></ul>"
            
            print("{\"correct\": "+correct+", \"score\": "+score+", \"msg\": \"<div><p><b>Test failed Error</b></p>"+message+"</div>\"}", end='')
    else:
        splitted = message.split("</p><pre>")
        splitted[0] = cgi.escape(splitted[0]).replace("\"", "&#34;") # Transformation for html.
        splitted[1] = cgi.escape(splitted[1].split("</pre>")[0]).replace("\"", "&#34;")+"</pre>" # Transformation for html.
        message = splitted[0].replace("\n","<br />")+"</p><pre>"+splitted[1].replace("\n", "\\n") # Tranformation for html.
        message = message.replace("%","&#37;") # Transformation for html.
        if error == 1:
            print("{\"correct\": "+correct+", \"score\": "+score+", \"msg\": \"<div><p><b>Compilation Error</b></p><br /><p>"+message+"</div>\"}", end='')
        else:
            print("{\"correct\": "+correct+", \"score\": "+score+", \"msg\": \"<div><p><b>Runtime Error</b></p><br /><p>"+message+"</div>\"}", end='')

# Main "check student answer" method.
# out contains what was printed by task.oz
def checkStdout(out):
    if out.strip() == "Hello World!": # Check if "Hello World!" is printed.
        JSON('Printed message: Hello World!','OK')
    else:
        if not "!" in out and "Hello World" in out: # Tip if "!" is forgotten.
            JSON('Your answer: '+out.strip()+'Expected answer: Hello World!<%%%%%>You have forgotten "!" at the end of the message you have printed.','KO')
        else:
            JSON('Your answer: '+out.strip()+'Expected answer: Hello World!','KO')

# 1) Check if there is a runtime error.
# 2) If there is no runtime error, check the answer.
# 3) If there is no runtime error, and if there is no answer, check if there is a compilation error.
# 2 is before 3 because otherwise, warnings could block the process (it would say there is a compilation error, 
# even if the code is correct but raises warnings.)
with open("errR.txt", "r") as errR: # 1)
    errRs = errR.read()
    if not errRs == "":
        runningerror(errRs)
    #else:
    error = 0
    with open("out.txt","r") as out: # 2)
        outs = out.read()
        if not outs == "":
            checkStdout(outs)
        else:
            with open("errC.txt", "r") as errC: # 3)
                errCs = errC.read()
                if not errCs == "":
                    compileerror(errCs)
                else:
                    # This case: no error message but the output file is empty for an unkown reason.
                    print("{\"correct\": false, \"score\": 0, \"msg\": \"<div><p><b>Other Error</b></p><p>"+"Check that there is no (infinite) wait that an unbound variable is bound."+"</p></div>\"}", end='')
