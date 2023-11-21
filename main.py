from flask import Flask, request, render_template, redirect, send_from_directory
import PyPDF2
import re
import glob
import os
from simplemma import lemmatize
from index_pdf import index_document

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # Adjust the value as needed
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
def view_or_index(filename=None):
    if filename:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)
    else:
        uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
        return render_template('index.html', uploaded_files=uploaded_files)


@app.route('/search', methods=['POST'])
def search():
    folder_path = request.form['folder_path']

    if not os.path.exists(folder_path):
        return render_template('error.html', message='Folder does not exist.')

    document_paths = glob.glob(os.path.join(folder_path, '*.pdf'))
    if not document_paths:
        return render_template('error.html', message='No PDF files found in the specified folder.')

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
        return render_template('links.html', links=links, filename=file.filename)


@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    links = extract_links_from_pdf(file_path)
    return render_template('links.html', filename=filename, links=links)


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run()
