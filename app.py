from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import os
from werkzeug.utils import secure_filename
# Add sumy imports for summarization
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.utils import get_stop_words

# Supported languages for Sumy
SUMY_LANGUAGES = [
    ("english", "English"),
    ("french", "French"),
    ("german", "German"),
    ("spanish", "Spanish"),
    ("italian", "Italian"),
    ("portuguese", "Portuguese"),
    ("russian", "Russian"),
    ("czech", "Czech"),
    ("slovak", "Slovak")
]

app = Flask(__name__)
app.secret_key = 'owlai_secret_key'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SESSION_TYPE'] = 'filesystem'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def simple_summarize(text, sentence_count=3, language="english"):
    parser = PlaintextParser.from_string(text, Tokenizer(language))
    summarizer = LsaSummarizer()
    summarizer.stop_words = get_stop_words(language)
    summary = summarizer(parser.document, sentence_count)
    return ' '.join(str(sentence) for sentence in summary)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/input', methods=['GET', 'POST'])
def input_page():
    summary = None
    user_input = ''
    error = None
    used_textbox = False
    selected_language = 'english'
    # Load summary history from session
    if 'history' not in session:
        session['history'] = []
    if request.method == 'POST':
        sentence_count = int(request.form.get('sentence_count', 3))
        selected_language = request.form.get('language', 'english')
        if 'user_input' in request.form and request.form.get('user_input') and (not request.files['file'] or request.files['file'].filename == ''):
            user_input = request.form.get('user_input')
            used_textbox = True
        elif 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            if file and allowed_file(file.filename):
                file.stream.seek(0)
                user_input = file.read().decode('utf-8')
                used_textbox = False
            else:
                error = 'Invalid file type. Only .txt files are allowed.'
        else:
            error = 'Please enter text or upload a file.'
        if user_input:
            try:
                # Remove all previous flash messages before summarizing
                session['_flashes'] = []
                flash('Summarizing... Please wait.', 'info')
                summary = simple_summarize(user_input, sentence_count=sentence_count, language=selected_language)
                # Save to history
                session['history'].append(summary)
                session.modified = True
                # Remove the 'Summarizing...' message and show only success
                session['_flashes'] = [f for f in session.get('_flashes', []) if f[1] != 'Summarizing... Please wait.']
                flash('Summarized successfully!', 'success')
            except Exception as e:
                error = f'Error during summarization: {str(e)}'
    return render_template('input.html', summary=summary, user_input=(user_input if used_textbox else ''), error=error, history=session.get('history', []), languages=SUMY_LANGUAGES, selected_language=selected_language)

@app.route('/download_summary')
def download_summary():
    summary = request.args.get('summary', '')
    buf = io.BytesIO()
    buf.write(summary.encode('utf-8'))
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='summary.txt', mimetype='text/plain')

@app.route('/display')
def display():
    value = request.args.get('value', '')
    return render_template('display.html', value=value)

if __name__ == '__main__':
    app.run(debug=True)
