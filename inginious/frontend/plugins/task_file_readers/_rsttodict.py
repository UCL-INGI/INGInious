# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

"""" Helper package for tasks_rst_file_manager. DEPRECATED """

import collections
import re
from abc import abstractmethod

from docutils import core, nodes
from docutils.parsers.rst import Parser, Directive, directives
from docutils.writers import UnfilteredWriter


class Question(nodes.General, nodes.Element):
    id = None
    name = None
    header = None
    type = None
    language = None
    answer = None
    multiple = None
    limit = None


class Box(nodes.General, nodes.Element):
    type = None
    content = None
    maxchars = None
    lines = None
    language = None


class Choice(nodes.General, nodes.Element):
    text = None
    valid = None


class BaseDirective(Directive):
    has_content = True

    @abstractmethod
    def get_node(self):
        return None

    def run(self):
        node = self.get_node()
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]


class QuestionDirective(BaseDirective):
    required_arguments = 1
    option_spec = {
        'type': str,
        'language': str,
        'answer': str,
        'multiple': bool,
        'limit': int
    }

    def get_node(self):
        return Question()

    def run(self):
        node = BaseDirective.run(self)[0]
        node.id = self.arguments[0]
        node.header = '\n'.join(self.content)
        match = re.search(r'\.\.[ \t]+(positive|negative|box)::', node.header)
        if match:
            node.header = node.header[:match.start()].strip()
        else:
            node.header = node.header.strip()
        for option, value in list(self.options.items()):
            setattr(node, option, value)
        return [node]


class BoxDirective(Directive):
    has_content = True
    option_spec = {
        'type': str,
        'maxchars': int,
        'lines': int,
        'language': str
    }

    def run(self):
        node = Box()
        for option, value in list(self.options.items()):
            setattr(node, option, value)
        node.content = '\n'.join(self.content)
        return [node]


class PosNegDirective(Directive):
    has_content = True

    # This has to be replaced in subclasses
    valid = None

    def run(self):
        node = Choice()
        node.text = '\n'.join(self.content)
        node.valid = self.valid
        return [node]


class PositiveDirective(PosNegDirective):
    valid = True


class NegativeDirective(PosNegDirective):
    valid = False


class TitleParser(Parser):
    symbols = r'[!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~]'
    context = None

    def parse(self, inputstring, document):
        pattern = (r'(?:' + TitleParser.symbols + r'+\s)?.+\s' + TitleParser.symbols
                   + r'+\s+(?:(?::.+:.*\s)*)((?:.*\s)*?)(?:'
                   + TitleParser.symbols + r'+\s)?.+\s' + TitleParser.symbols + r'+')
        self.context = re.search(pattern, inputstring).group(1).strip('\n\r')
        Parser(self).parse(inputstring, document)


class Writer(UnfilteredWriter):
    docinfo_types = {
        'context': str,
        'order': int,
        'name': str,
        'accessible': str,
        'limit-time': int,
        'limit-memory': int,
        'limit-output': int,
        'environment': str
    }

    parser = None
    output = {}

    def translate(self):
        self.validate()
        self.docinfo()
        title = self.document.next_node(nodes.title)
        if title:
            self.output['name'] = title.astext()
        if self.parser.context and len(self.parser.context) > 0:
            self.output['context'] = self.parser.context
        self.process_questions()

    def validate(self):
        docinfo = self.document.next_node(nodes.docinfo)
        if docinfo:
            for field in docinfo.traverse(nodes.field):
                field_name = field.next_node(nodes.field_name).astext()
                field_body = field.next_node(nodes.field_body).astext()
                try:
                    Writer.docinfo_types[field_name](field_body)
                except KeyError:
                    raise StructureError('Invalid document option: ' + field_name + '.')
                except ValueError:
                    raise StructureError('Invalid value for ' + field_name + ' option: ' + field_body + '.')
        questions = self.document.traverse(Question)
        if len(questions) == 0:
            raise StructureError('There must be at least one question in your document.')
        for question in questions:
            qtype = get_type(question.type)
            qtype.validate(question)

    def docinfo(self):
        docinfo = self.document.next_node(nodes.docinfo)
        if not docinfo:
            return
        author = docinfo.next_node(nodes.author)
        if author:
            self.output['author'] = [s.strip() for s in author.astext().split(',')]
            if len(self.output['author']) == 1:
                self.output['author'] = self.output['author'][0]
        self.output['limits'] = {}
        for field in docinfo.traverse(nodes.field):
            field_name = field.next_node(nodes.field_name).astext()
            field_body = field.next_node(nodes.field_body).astext()
            if field_name == 'accessible':
                if field_body == 'true':
                    self.output['accessible'] = True
                    continue
                if field_body == 'false':
                    self.output['accessible'] = False
                    continue
            match = re.match('^limit-(.*)$', field_name)
            if match:
                self.output['limits'][match.group(1)] = Writer.docinfo_types[field_name](field_body)
            else:
                self.output[field_name] = Writer.docinfo_types[field_name](field_body)

    def process_questions(self):
        self.output['problems'] = collections.OrderedDict()
        for question in self.document.traverse(Question):
            name = question.parent.next_node(nodes.title)
            if name:
                question.name = name.astext()
            infos = {}
            for option in QuestionDirective.option_spec:
                value = getattr(question, option)
                if value:
                    infos[option] = value
            if question.name:
                infos['name'] = question.name
            if question.header and len(question.header) > 0:
                infos['header'] = question.header
            self.process_boxes(question, infos)
            self.process_choices(question, infos)
            self.output['problems'][question.id] = infos

    def process_boxes(self, question, infos):
        boxes = collections.OrderedDict()
        bid = 1
        for box in question.traverse(Box):
            boxId = 'boxId' + str(bid)
            boxes[boxId] = {}
            for option in BoxDirective.option_spec:
                value = getattr(box, option)
                if option == 'maxchars':
                    option = 'maxChars'
                if value:
                    boxes[boxId][option] = value
                if box.content:
                    boxes[boxId]['content'] = box.content
            bid += 1
        if len(boxes) > 0:
            infos['boxes'] = boxes

    def process_choices(self, question, infos):
        choices = []
        for choice in question.traverse(Choice):
            choices.append({
                'text': choice.text,
                'valid': choice.valid
            })
        if len(choices) > 0:
            infos['choices'] = choices


def get_type(ttype):
    if ttype == 'code':
        return Code()
    if ttype == 'code-single-line':
        return CodeSingleLine()
    if ttype == 'match':
        return Match()
    if ttype == "multiple-choice":
        return MultipleChoice()
    return UnknownType()


class StructureError(Exception):
    pass


class Type(object):
    def validate(self, question):
        pass


class Code(Type):
    def validate(self, question):
        for box in question.traverse(Box):
            if not box.type:
                raise StructureError('Every box directive must have a type option.')
            if box.type == 'text' and not box.content:
                raise StructureError('A box directive with a text type must have a content option.')


class CodeSingleLine(Type):
    pass


class Match(Type):
    def validate(self, question):
        if not question.answer:
            raise StructureError('A match type question must have an answer option.')


class MultipleChoice(Type):
    def validate(self, question):
        for choice in question.traverse(Choice):
            if not choice.text or len(choice.text) == 0:
                raise StructureError('Every positive and negative directive must have a content.')


class UnknownType(Type):
    def validate(self, question):
        raise StructureError('Unknown type for the question directive.')


def rst2dict(rst_string):
    directives.register_directive('question', QuestionDirective)
    directives.register_directive('box', BoxDirective)
    directives.register_directive('positive', PositiveDirective)
    directives.register_directive('negative', NegativeDirective)
    parser = TitleParser()
    writer = Writer()
    writer.parser = parser
    return core.publish_string(source=rst_string, parser=parser, writer=writer)
