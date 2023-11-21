class Document:

    def __init__(self, title, path):
        self.title = title
        self.path = path
        self.terms = {}
        self.score = 0.0

    def add_word(self, word):
        if not word in self.terms:
            self.terms[word] = 1
        else:
            self.terms[word] += 1
