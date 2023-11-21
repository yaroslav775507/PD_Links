from flask import Flask, render_template, request
import glob
import os
from werkzeug.utils import secure_filename
from simplemma import lemmatize
from index_pdf import index_document

app = Flask(__name__)

# Set the upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index():
    return render_template('index.html')


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


if __name__ == '__main__':
    # Ensure the 'uploads' folder exists
    os.makedirs('uploads', exist_ok=True)

    app.run(debug=True, port=5000)
