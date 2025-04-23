from io import BytesIO
from pdfminer.high_level import extract_text as pdfminer_extract_text
from pdfplumber import open as pdfplumber_open
from docx import Document

def extract_text_from_file(file):
    try:
        file_content = file.read()
        file.seek(0)  # Возвращаем указатель в начало файла
        
        if file.filename.endswith('.pdf'):
            try:
                # Попробуем через pdfminer
                return pdfminer_extract_text(BytesIO(file_content))
            except Exception:
                # Если pdfminer не сработал, пробуем pdfplumber
                try:
                    with pdfplumber_open(BytesIO(file_content)) as pdf:
                        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
                except Exception as e:
                    raise ValueError(f"PDF processing failed: {str(e)}")
        
        elif file.filename.endswith('.docx'):
            try:
                doc = Document(BytesIO(file_content))
                return "\n".join([p.text for p in doc.paragraphs if p.text])
            except Exception as e:
                raise ValueError(f"DOCX processing failed: {str(e)}")
        
        # Для текстовых файлов
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError("Could not decode text file (UTF-8 required)")
            
    except Exception as e:
        raise ValueError(f"File processing error: {str(e)}")")
