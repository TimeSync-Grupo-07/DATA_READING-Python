from PyPDF2 import PdfReader

def pdf_to_json(pdf_stream):
    """
    Converte um PDF em um dicionário JSON simples.
    Você pode customizar a extração conforme o formato dos relatórios.
    """
    reader = PdfReader(pdf_stream)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    # Exemplo de estrutura JSON simplificada
    json_data = {
        "lines": [line.strip() for line in text.split("\n") if line.strip()],
        "page_count": len(reader.pages)
    }
    return json_data
