from flask import Flask, request, render_template, redirect
from flask import send_from_directory
import PyPDF2
import re
from flask import Flask, render_template, request
import glob
import os
from werkzeug.utils import secure_filename
from simplemma import lemmatize
from index_pdf import index_document

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
url_pattern = r'https?://\S+'

def extract_links_from_pdf(file_path):
    links = []
    with open(file_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text = page.extract_text()
            found_urls = re.findall(url_pattern, text)
            links.extend(found_urls)
    return links

@app.route('/view_pdf/<filename>')
def view_pdf(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)
@app.route('/')
def index():
    # Получаем список уже загруженных файлов
    uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', uploaded_files=uploaded_files)
# Функция адиля
@app.route('/search', methods=['POST'])
def search():
    # Get the uploaded file
    uploaded_file = request.files['file']

    # Save the uploaded file to the uploads folder
    if uploaded_file:
        filename = secure_filename(uploaded_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(file_path)

        # Use the uploaded file for processing
        document_paths = [file_path]
    else:
        # If no file is uploaded, use the provided path
        path = request.form['path']
        document_paths = glob.glob(os.path.join(path, '*.pdf'))

    print('Indexing...')
    documents = [index_document(path) for path in document_paths]
    print('Done!')

    all_terms = {}
    for doc in documents:
        for word, freq in doc.terms.items():
            if word not in all_terms:
                all_terms[word] = freq
            else:
                all_terms[word] += freq

    prompt = request.form['prompt']
    num_matches = int(request.form['num_matches'])

    results = []
    for word in prompt.split(' '):
        word = lemmatize(word, lang=('ru', 'en'))
        for doc in documents:
            if word not in doc.terms:
                continue
            tf = doc.terms[word]
            df = all_terms[word]
            doc.score += tf / df

    documents.sort(key=lambda x: x.score, reverse=True)
    for doc in documents[:num_matches]:
        result = {
            'path': doc.path,
            'title': doc.title,
            'score': f'{doc.score:.2f}'
        }
        results.append(result)

    return render_template('results.html', results=results)
@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        links = extract_links_from_pdf(filename)
        return render_template('links.html', links=links)

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Ищем ссылки в загруженном PDF-файле
    links = extract_links_from_pdf(file_path)

    return render_template('links.html', filename=filename, links=links)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)
    app.run()
