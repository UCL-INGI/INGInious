class ParsableText:
    def __init__(self,content,mode="rst"):
        if mode not in ["rst","HTML"]:
            raise Exception("Unknown text parser: "+ mode)
        self.content = content
        self.mode = mode
    def parse(self):
        return "" #TODO