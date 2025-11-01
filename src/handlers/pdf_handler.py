from utils.pdf_to_json import pdf_to_json

def process_pdf(pdf_stream):
    """Recebe o PDF em memória e retorna o JSON extraído."""
    try:
        return pdf_to_json(pdf_stream)
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return {"error": str(e)}
