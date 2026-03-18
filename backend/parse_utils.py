import io
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import docx
except ImportError:
    docx = None

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    if not pdfplumber:
        return "pdfplumber not installed"
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        print(f"Error parsing PDF: {e}")
    return text

def extract_text_from_docx(file_bytes: bytes) -> str:
    text = ""
    if not docx:
        return "python-docx not installed"
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error parsing DOCX: {e}")
    return text

def extract_text_from_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode('utf-8')
    except Exception:
        return file_bytes.decode('latin-1', errors='ignore')

def parse_file(filename: str, file_bytes: bytes) -> str:
    filename_lower = filename.lower()
    if filename_lower.endswith('.pdf'):
        return extract_text_from_pdf(file_bytes)
    elif filename_lower.endswith('.docx') or filename_lower.endswith('.doc'):
        return extract_text_from_docx(file_bytes)
    else:
        # Fallback treat as text
        return extract_text_from_txt(file_bytes)
