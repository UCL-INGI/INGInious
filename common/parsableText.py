from docutils import core


class ParsableText:
    """Allow to parse a string with different parsers"""
    
    def __init__(self,content,mode="rst"):
        """Init the object. Content is the string to be parsed. Mode is the parser to be used. Currently, only rst(reStructuredText) and HTML are supported"""
        if mode not in ["rst","HTML"]:
            raise Exception("Unknown text parser: "+ mode)
        self.content = content
        self.mode = mode
    
    def parse(self):
        """Returns parsed text"""
        if self.mode == "HTML":
            return self.content
        else:
            return self.rst(self.content)
    
    def __str__(self):
        """Returns parsed text"""
        return self.parse()
    
    def __unicode__(self):
        """Returns parsed text"""
        return self.parse()
    
    def rst(self,s):
        """Parses reStructuredText"""
        parts = core.publish_parts(source=s,writer_name='html')
        return parts['body_pre_docinfo']+parts['fragment']