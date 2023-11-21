from PyPDF2 import PdfReader
import nltk
from simplemma import lemmatize

from document import Document

def index_document(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
        break

    title = reader.metadata.title
    if title == None:
        title = reader.pages[0].extract_text().partition('\n')[0]
        # if len(reader.outline) > 0:
            # title = reader.outline[0].title
    document = Document(title, path)

    # делим текст на слова
    words = nltk.word_tokenize(text)
    words.remove

    stopwords = { ',', '.', '!', '?', '(', ')' }
    words = [word for word in words if not word.lower() in stopwords]

    for word in words:
        # отсекаем короткие слова
        if len(word) > 2:
            w = word.lower()
            w = lemmatize(w, lang=('ru', 'en'))
            document.add_word(w)

    return document
