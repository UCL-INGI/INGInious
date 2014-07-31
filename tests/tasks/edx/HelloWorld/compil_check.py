# -*- coding: utf8 -*-
# Author: Adrien Bibal
# Date: 2014
# This file add tips in compilation error message. 
# The goal is to provide more information in the case of errors raised by the compiler.

# file_path is the path to the file containing the student answer integrated in the oz file containing the correction.
# checkLowercaseVar checks if a variable with a lower case has been assigned. 
# (Oz identifiers always have to begin with a capital letter, except in the case of class attributes (e.g. attribute := 1).
# Returns a message containing all the problematic variables if they exists, returns "" otherwise.
def checkLowercaseVar(file_path):
    with open(file_path) as question_file:
        varFault = "" # The name of the problematic variable.
        for line in question_file:
            position = line.find("=") # If there is at least one "=", there is an assignation.
            # Two cases are checked:
            # 1) "=" is not the first char of the line and there isn't ":" right before. This case is the cell assignation.
            # 2) "=" is not the last char of the line and there isn't another "=" right after. This case is the equality check.
            if (position > 0 and line[position-1] != ":") and (position < len(line)+1 and line[position+1] != "="):
                checkingVar = False # if True, then we are currently reading the variable name.
                var = "" # Will contain the variable name
                for index in range(position-1, -1, -1): # From the position right before "=" to the first char of the variable name.
                    # Consider lowercases, uppercases and spaces.
                    if line[index].islower() or line[index].isupper() or line[index] == " ":
                        # If I'm on a space and I'm currently reading a variable name, 
                        # then the space is the one before the first char of the name (we can stop).
                        if line[index] == " " and checkingVar:
                            if not var[0].isupper(): # If the first char is not a capital letter...
                                varFault += "A variable must begin with a capital letter! Please check: "+var+"\n"
                            break
                        # If I'm not on a space and I don't read the variable name yet,
                        # then begin reading the variable name.
                        elif line[index] != " " and not checkingVar:
                            var = line[index] + var
                            checkingVar = True
                        # If I'm currently reading the variable name and I'm not on a space,
                        # then continue to read the variable name.
                        elif line[index] != " " and checkingVar:
                            var = line[index] + var
    # Return the message ("" if nothing has been found).
    return varFault

# file_path is the path to the file containing the student answer integrated in the oz file containing the correction.
# checkDeclare checks if "declare" has been used in the exercise (it should not be used).
# If "declare" is found, returns a message explaining to the student that he does not have to use "declare".
def checkDeclare(file_path):
    with open(file_path) as question_file:
        declareFound = False
        # For each line, check if "declare" is found.
        for line in question_file:
            if "declare " in line or "declare\n" in line:
                declareFound = True
                break
        if declareFound:
            return "You do not have to use \"declare\" in your code!\n"
        else:
            return ""

# msg is the error message given by the compiler.
# checkNotIntroduced checks if the error message refers to a problem of variable introduction.
# If this is the case, add more information for the student in the message.
def checkNotIntroduced(msg):
    error_message = ""
    # First, check if the error message is the one expected by this function.
    if "not introduced" in msg:
        for line in msg.split("\n"):
            if "not introduced" in line:
                var = line.split(" not introduced")[0].split("variable ")[1] # Extract the variable name in the message.
                error_message += "The variable \""+var+"\" in your code has not been introduced/declared.\n"
    # error_message is the message to add to the compilation error message.
    return error_message

# msg is the error message given by the compiler.
# checkCallWithAtom checks if the error message refers to a problem of variable call but with lowercase.
def checkCallWithAtom(msg):
    error_message = ""
    # First, check if the error message is the one expected by this function.
    if "applying non-procedure and non-object\n%**\n%** Value found: " in msg:
        msg = msg.split("applying non-procedure and non-object\n%**\n%** Value found: ") # msg is now an array.
        for i in range(1, len(msg)): # For each "applying non-procedure and non-object...", insert more information in the message.
            error_message += "Did you try to call a procedure/function named \""+msg[i].split("\n")[0]+"\"? Check you did not forget any uppercase.\n"

    # error_message is the message to add to the compilation error message.
    return error_message

# msg is the error message given by the compiler.
# checkIllegalArity checks if the error message refers to an arity problem.
# If this is the case, add more information for the student in the message.
def checkIllegalArity(msg):
    error_message = ""
    # First, check if the error message is the one expected by this function.
    if "illegal arity in application" in msg:
        msg = msg.split("illegal arity in application") # msg is now an array.
        for i in range(1, len(msg)):
            if "Application (names): " in msg[i]: # Find the line containing the name.
                name = msg[i].split("Application (names):  ")[1]
                if "\n%**" in name:
                    name = name.split("\n%**")[0]
                    error_message += "It seems you used \""+name+"\" with a wrong arity (wrong number of arguments for instance).\n"
    if not error_message == "": # Add a tip at the end of the message.
        error_message += "Maybe this tip can help: if you use functions, do not forget to \"handle\" the returned value.\n"
    return error_message

# msg is the error message given by the compiler.
# checkIllegalUseOfNesting checks if the corresponding error message ("illegal use of nesting marker") is given by the compiler.
# If this is the case, add a tip to the error message.
def checkIllegalUseOfNesting(msg):
    error_message = ""
    # First, check if the error message is the one expected by this function.
    if "illegal use of nesting marker" in msg:
        # Adding a tip at the end of the error message.
        error_message = "Maybe you used in a bad way the symbol \"$\" (which is used as a nesting marker).\n"
    return error_message

# msg is the error message given by the compiler.
# checkParserError checks if the error message is "Parse error" message.
# If this is the case, add a tip to the error message.
def checkParseError(msg):
    error_message = ""
    # First, check if the error message is the one expected by this function.
    if "Parse error" in msg:
        # Adding a tip at the end of the error message.
        error_message = "The message \"Parse error\" often means that you have forgotten a closing bracket, a \"end\", etc. Or maybe, there are too much brackets, \"end\", etc.! Take a look at the error line. The line may be incorrect because if an end is missing, for instance, it looks too far away for the error.\n"
    return error_message

# msg is the error message given by the compiler.
# checkEqualityConstraint checks if the error message is about the failure of an equality constraint.
# If this is the case, add a tip to the error message.
def checkEqualityConstraint(msg): # (WARNING: possible conflict with checkLowerCase)
    error_message = ""
    if "equality constraint failed" in msg:
        # Adding a tip at the end of the error message.
        error_message = "About the \"equality constraint failed\", did you forget to put a capital letter to the identifier? Exemple: Identifier = 42\n"
    return error_message

# msg is the error message given by the compiler.
# checkExpressionStatement checks if there is an "expression at statement position" error message.
# If this is the case, add a tip including the problematic line to the error message.
def checkExpressionStatement(msg):
    error_message = ""
    if "expression at statement position" in msg:
        msg = msg.split("expression at statement position")
        error_message = "At line(s):"
        lines = ""
        for i in range(1, len(msg)):
            if "in file \"Oz\", line " in msg[i]: # Consider the error message line containing the problematic line number.
                lines += " " + msg[i].split("in file \"Oz\", line ")[1].split(", column ")[0] + "," # Find and add this line number.
        # Adding the tip
        error_message += lines + " it seems you used an expression (did you try to return something?) instead of a statement (for instance X = 42).\n"
    return error_message
