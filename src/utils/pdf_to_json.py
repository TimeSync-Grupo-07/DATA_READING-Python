from PyPDF2 import PdfReader
import re
from datetime import datetime

def pdf_to_json(pdf_stream):
    """
    Converte um PDF de espelho de ponto em JSON estruturado e tolerante a erros.
    Nenhuma exceção crítica deve interromper a execução.
    """
    try:
        reader = PdfReader(pdf_stream)
    except Exception as e:
        return _error_json(f"Falha ao ler PDF: {e}")

    full_text = ""
    for page in getattr(reader, "pages", []):
        try:
            full_text += page.extract_text() or ""
        except Exception:
            continue

    structured_data = {}
    try:
        structured_data = parse_ponto_text(full_text)
    except Exception as e:
        structured_data = {"header": {}, "days": []}

    json_data = {
        "metadata": {
            "document_type": "espelho_ponto",
            "page_count": len(getattr(reader, "pages", [])),
            "extraction_date": datetime.now().isoformat(),
            "file_format_version": "1.0"
        },
        "header_info": safe_call(extract_header_info, full_text, default={}),
        "period_summary": safe_call(extract_period_summary, structured_data, default={}),
        "daily_records": safe_call(extract_daily_records, structured_data, default=[]),
        "raw_lines": [line.strip() for line in full_text.split("\n") if line.strip()],
        "processing_stats": {
            "total_days": len(structured_data.get("days", [])),
            "total_records": safe_call(count_total_records, structured_data, default=0),
            "work_days": safe_call(count_work_days, structured_data, default=0),
            "compensated_days": safe_call(count_compensated_days, structured_data, default=0)
        }
    }

    return json_data


# ============================================================
# FUNÇÕES PRINCIPAIS DE PARSING
# ============================================================

def parse_ponto_text(text):
    """Faz parsing do texto do espelho de ponto em estrutura intermediária."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    structured = {
        "header": {},
        "days": []
    }

    current_day = None

    for i, line in enumerate(lines):
        try:
            # Cabeçalho
            if "Espelho de Ponto" in line:
                structured["header"]["title"] = line
                continue
            if "Colaborador" in line:
                structured["header"]["employee"] = extract_employee_info(line)
                continue
            if "Período" in line:
                structured["header"]["period"] = extract_period_info(line)
                continue

            # Nova data
            date_match = re.match(r"(\d{2}/\d{2}/\d{4})", line)
            if date_match:
                if current_day:
                    structured["days"].append(current_day)

                current_day = {
                    "date": date_match.group(1),
                    "records": []
                }

                record_data = parse_record_line(line)
                if record_data:
                    current_day["records"].append(record_data)
            elif current_day and is_record_line(line):
                record_data = parse_record_line(line)
                if record_data:
                    current_day["records"].append(record_data)

        except Exception:
            continue

    if current_day:
        structured["days"].append(current_day)

    return structured


# ============================================================
# EXTRAÇÕES E VALIDAÇÕES
# ============================================================

def extract_employee_info(line):
    """Extrai informações do colaborador."""
    try:
        match = re.search(r"Colaborador\(a\):\s*(.+?)\s*\(Matrícula:\s*(\d+)\)", line)
        if match:
            return {
                "name": match.group(1).strip(),
                "registration": match.group(2).strip()
            }
    except Exception:
        pass
    return {"name": None, "registration": None}

def extract_period_info(line):
    """Extrai o período do espelho."""
    try:
        match = re.search(r"Período:\s*(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}/\d{2}/\d{4})", line)
        if match:
            return {
                "start_date": match.group(1),
                "end_date": match.group(2),
                "month_year": match.group(1)[3:] if match.group(1) else None
            }
    except Exception:
        pass
    return {"start_date": None, "end_date": None, "month_year": None}

def is_record_line(line):
    """Verifica se a linha representa um registro."""
    excluded_terms = ["Data", "Ocorrência", "Justificativa", "Projetos", "Ticket", "Início", "Saída", "Inativo", "Horas", "Motivo"]
    return not any(term in line for term in excluded_terms) and len(line) > 5

def parse_record_line(line):
    """Interpreta linha de registro com tolerância a erros."""
    try:
        parts = re.split(r"\s{2,}", line.strip())
        record = {
            "occurrence_type": parts[1] if len(parts) > 1 else None,
            "justification": parts[2] if len(parts) > 2 else None,
            "projects": parts[3] if len(parts) > 3 else None,
            "ticket": parts[4] if len(parts) > 4 else None,
            "start_time": parts[5] if len(parts) > 5 else None,
            "end_time": parts[6] if len(parts) > 6 else None,
            "inactive_time": parts[7] if len(parts) > 7 else None,
            "hours": parts[8] if len(parts) > 8 else None,
            "reason": parts[9] if len(parts) > 9 else None
        }
        record["is_compensated"] = "Compensado" in (record["occurrence_type"] or "")
        record["is_manual"] = "Manual" in (record["occurrence_type"] or "")
        record["is_overtime"] = "extra" in (record["occurrence_type"] or "").lower()
        return record
    except Exception:
        return None


# ============================================================
# EXTRAÇÕES DE ALTO NÍVEL
# ============================================================

def extract_header_info(text):
    """Extrai cabeçalho principal (colaborador, período)."""
    header = {"employee": {"name": None, "registration": None}, "period": {"start": None, "end": None}}
    try:
        emp = re.search(r"Colaborador\(a\):\s*(.+?)\s*\(Matrícula:\s*(\d+)\)", text)
        per = re.search(r"Período:\s*(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}/\d{2}/\d{4})", text)
        if emp:
            header["employee"] = {"name": emp.group(1).strip(), "registration": emp.group(2).strip()}
        if per:
            header["period"] = {"start": per.group(1), "end": per.group(2)}
    except Exception:
        pass
    return header

def extract_period_summary(structured_data):
    """Extrai resumo das horas e dias."""
    days = structured_data.get("days", [])
    work, overtime, project = 0, 0, 0

    for day in days:
        for rec in day.get("records", []):
            try:
                mins = parse_hours_to_minutes(rec.get("hours", "0"))
                if rec.get("is_overtime"):
                    overtime += mins
                elif "Projeto" in (rec.get("occurrence_type") or ""):
                    project += mins
                else:
                    work += mins
            except Exception:
                continue

    return {
        "total_work_hours": format_minutes_to_hours(work),
        "total_overtime_hours": format_minutes_to_hours(overtime),
        "total_project_hours": format_minutes_to_hours(project),
        "work_days_count": len([d for d in days if not all(r.get("is_compensated") for r in d.get("records", []))])
    }

def extract_daily_records(structured_data):
    """Gera lista de registros diários prontos para inserção futura."""
    records = []
    for d in structured_data.get("days", []):
        try:
            day = {
                "date": d.get("date"),
                "is_compensated": all(r.get("is_compensated") for r in d.get("records", [])),
                "records": []
            }
            for r in d.get("records", []):
                day["records"].append({
                    "occurrence_type": r.get("occurrence_type"),
                    "justification": r.get("justification"),
                    "projects": r.get("projects"),
                    "ticket": r.get("ticket"),
                    "start_time": r.get("start_time"),
                    "end_time": r.get("end_time"),
                    "inactive_time": r.get("inactive_time"),
                    "hours": r.get("hours"),
                    "reason": r.get("reason"),
                    "is_manual_entry": r.get("is_manual", False),
                    "is_overtime": r.get("is_overtime", False)
                })
            records.append(day)
        except Exception:
            continue
    return records


# ============================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================

def parse_hours_to_minutes(h):
    try:
        if not h:
            return 0
        if ":" in h:
            hh, mm = h.split(":")
            return int(hh) * 60 + int(mm)
        return int(h) * 60
    except Exception:
        return 0

def format_minutes_to_hours(m):
    try:
        h = m // 60
        mm = m % 60
        return f"{h}:{mm:02d}"
    except Exception:
        return "0:00"

def count_total_records(data):
    return sum(len(d.get("records", [])) for d in data.get("days", []))

def count_work_days(data):
    return len([d for d in data.get("days", []) if not all(r.get("is_compensated") for r in d.get("records", []))])

def count_compensated_days(data):
    return len([d for d in data.get("days", []) if all(r.get("is_compensated") for r in d.get("records", []))])

def safe_call(fn, *args, default=None):
    try:
        return fn(*args)
    except Exception:
        return default

def _error_json(msg):
    """Retorna um JSON padrão de erro de extração."""
    return {
        "metadata": {"document_type": "espelho_ponto", "extraction_date": datetime.now().isoformat()},
        "error": True,
        "message": msg,
        "header_info": {},
        "daily_records": [],
        "period_summary": {},
        "raw_lines": [],
        "processing_stats": {}
    }
