# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Helper package for tasks_rst_file_manager. DEPRECATED """

main_options = ['order', 'environment']
limits_options = ['time', 'memory', 'output']
question_options = ['type', 'language', 'answer', 'multiple', 'limit']
box_options = ['type', 'maxChars', 'lines', 'language']


def dict2rst(dict_obj):
    rst = ''
    if 'name' in dict_obj:
        rst += '=' * len(dict_obj['name']) + '\n'
        rst += dict_obj['name'] + '\n'
        rst += '=' * len(dict_obj['name']) + '\n\n'
        if 'author' in dict_obj:
            if isinstance(dict_obj['author'], str):
                rst += ':author: ' + dict_obj['author'] + '\n'
            else:
                rst += ':author: ' + ', '.join(dict_obj['author']) + '\n'
        if 'accessible' in dict_obj:
            if dict_obj['accessible']:
                rst += ':accessible: true\n'
            elif dict_obj['accessible'] == False:
                rst += ':accessible: false\n'
            else:
                rst += ':accessible: ' + dict_obj['accessible'] + '\n'
        for option in main_options:
            if option in dict_obj:
                rst += ':' + option + ': ' + str(dict_obj[option]) + '\n'
    if 'limits' in dict_obj:
        for option in limits_options:
            if option in dict_obj['limits']:
                rst += ':limit-' + option + ': ' + str(dict_obj['limits'][option]) + '\n'
    rst += '\n'
    if 'context' in dict_obj:
        rst += dict_obj['context'] + '\n\n'
    if 'problems' in dict_obj:
        for pid, problem in list(dict_obj['problems'].items()):
            if 'name' in problem:
                rst += problem['name'] + '\n'
                rst += '-' * len(problem['name']) + '\n\n'
            rst += '.. question:: ' + pid + '\n'
            for option in question_options:
                if option in problem:
                    rst += '\t:' + option + ': ' + str(problem[option]) + '\n'
            rst += '\n'
            if 'header' in problem:
                rst += tabularize(problem['header']) + '\n\n'
            if 'boxes' in problem:
                for pid, box in list(problem['boxes'].items()):
                    rst += '\t.. box:: ' + pid + '\n'
                    for option in box_options:
                        if option in box:
                            rst += '\t\t:' + option + ': ' + str(box[option]) + '\n'
                    if 'content' in box:
                        rst += '\n' + tabularize(box['content'], 2) + '\n'
                    rst += '\n'
            if 'choices' in problem:
                for choice in problem['choices']:
                    if 'valid' in choice and choice['valid']:
                        rst += '\t.. positive::\n'
                    else:
                        rst += '\t.. negative::\n'
                    if 'text' in choice:
                        rst += tabularize(choice['text'], 2) + '\n'
                    rst += '\n'
    return rst


def tabularize(string, n=1):
    return '\n'.join(['\t' * n + s for s in string.split('\n')])
