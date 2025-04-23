from flask import Blueprint, request, jsonify
from app.models import Document
from app.utils import pdf_parser, diff_tool
from concurrent.futures import ThreadPoolExecutor
from app import db

api_bp = Blueprint('api', __name__)
executor = ThreadPoolExecutor(4)

@api_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No filename"}), 400

    try:
        content = pdf_parser.extract_text_from_file(file)
        new_doc = Document(filename=file.filename, content=content)
        db.session.add(new_doc)
        db.session.commit()
        return jsonify({"id": new_doc.id, "filename": file.filename}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@api_bp.route('/compare', methods=['POST'])
def compare_docs():
    doc1 = Document.query.get(request.json['doc1_id'])
    doc2 = Document.query.get(request.json['doc2_id'])
    
    future = executor.submit(
        diff_tool.compare_texts, 
        doc1.content, 
        doc2.content
    )
    return jsonify({"html_diff": future.result()}), 200
