
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
import hashlib
from PyPDF2 import PdfReader
import datetime
import logging

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdf_comparison.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
db = SQLAlchemy(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

def allowed_file(filename):
    return '.' in filename and filename.lower().endswith('.pdf')

def extract_text_from_pdf(filepath):
    text = ""
    try:
        with open(filepath, 'rb') as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        raise
    return text

def calculate_file_hash(filepath):
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as file:
            buf = file.read()
            hasher.update(buf)
    except Exception as e:
        logger.error(f"Error calculating hash: {str(e)}")
        raise
    return hasher.hexdigest()

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part', 'success': False}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file', 'success': False}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF allowed', 'success': False}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        file_hash = calculate_file_hash(filepath)
        existing_doc = Document.query.filter_by(file_hash=file_hash).first()
        
        if existing_doc:
            os.remove(filepath)
            return jsonify({
                'message': 'File exists',
                'document_id': existing_doc.id,
                'success': True
            }), 200
        
        content = extract_text_from_pdf(filepath)
        new_doc = Document(filename=filename, file_hash=file_hash, content=content)
        
        db.session.add(new_doc)
        db.session.commit()
        
        return jsonify({
            'message': 'Upload successful',
            'document_id': new_doc.id,
            'success': True
        }), 201
    
    except Exception as e:
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({
            'error': f'Error: {str(e)}',
            'success': False
        }), 500

@app.route('/compare', methods=['POST'])
def compare_documents():
    if not request.is_json:
        return jsonify({'error': 'JSON required', 'success': False}), 400
    
    data = request.get_json()
    if not data or 'doc1_id' not in data or 'doc2_id' not in data:
        return jsonify({'error': 'IDs missing', 'success': False}), 400
    
    try:
        doc1 = Document.query.get(data['doc1_id'])
        doc2 = Document.query.get(data['doc2_id'])
        
        if not doc1 or not doc2:
            return jsonify({'error': 'Documents not found', 'success': False}), 404
        
        similarity = calculate_similarity(doc1.content, doc2.content)
        
        return jsonify({
            'doc1': doc1.filename,
            'doc2': doc2.filename,
            'similarity': similarity,
            'success': True
        })
    
    except Exception as e:
        return jsonify({
            'error': f'Error: {str(e)}',
            'success': False
        }), 500

@app.route('/documents', methods=['GET'])
def list_documents():
    try:
        documents = Document.query.order_by(Document.upload_date.desc()).all()
        docs_list = [{
            'id': doc.id,
            'filename': doc.filename,
            'upload_date': doc.upload_date.isoformat()
        } for doc in documents]
        
        return jsonify({
            'documents': docs_list,
            'success': True
        })
    
    except Exception as e:
        return jsonify({
            'error': f'Error: {str(e)}',
            'success': False
        }), 500

@app.route('/delete/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    try:
        doc = Document.query.get(doc_id)
        if not doc:
            return jsonify({'error': 'Not found', 'success': False}), 404
        
        db.session.delete(doc)
        db.session.commit()
        
        return jsonify({
            'message': 'Deleted',
            'success': True
        })
    
    except Exception as e:
        return jsonify({
            'error': f'Error: {str(e)}',
            'success': False
        }), 500

def calculate_similarity(text1, text2):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, text1, text2).ratio() * 100

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
