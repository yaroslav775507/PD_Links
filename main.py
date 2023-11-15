from flask import Flask, request, render_template, redirect
from flask import send_from_directory
import os
import PyPDF2
import re

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
