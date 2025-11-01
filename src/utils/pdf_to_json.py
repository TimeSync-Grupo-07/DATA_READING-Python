from PyPDF2 import PdfReader
import re
from datetime import datetime

def pdf_to_json(pdf_stream):
    """
    Converte um PDF de espelho de ponto em uma estrutura JSON elaborada
    com parsing inteligente dos dados tabulares.
    """
    reader = PdfReader(pdf_stream)
    
    # Extrai texto de todas as páginas
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() or ""
    
    # Processa o texto para estruturação
    structured_data = parse_ponto_text(full_text)
    
    json_data = {
        "metadata": {
            "document_type": "espelho_ponto",
            "page_count": len(reader.pages),
            "extraction_date": datetime.now().isoformat(),
            "file_format_version": "1.0"
        },
        "header_info": extract_header_info(full_text),
        "period_summary": extract_period_summary(structured_data),
        "daily_records": extract_daily_records(structured_data),
        "raw_lines": [line.strip() for line in full_text.split("\n") if line.strip()],
        "processing_stats": {
            "total_days": len(structured_data.get('days', [])),
            "total_records": count_total_records(structured_data),
            "work_days": count_work_days(structured_data),
            "compensated_days": count_compensated_days(structured_data)
        }
    }
    
    return json_data

def parse_ponto_text(text):
    """Faz parsing do texto do espelho de ponto"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    structured = {
        'header': {},
        'days': []
    }
    
    current_day = None
    
    for i, line in enumerate(lines):
        # Detecta cabeçalho
        if "Espelho de Ponto" in line:
            structured['header']['title'] = line
            continue
        if "Colaborador(a):" in line:
            structured['header']['employee'] = extract_employee_info(line)
            continue
        if "Período:" in line:
            structured['header']['period'] = extract_period_info(line)
            continue
        
        # Detecta linha de dados (formato de data)
        date_match = re.match(r'(\d{2}/\d{2}/\d{4})', line)
        if date_match:
            if current_day:
                structured['days'].append(current_day)
            
            current_day = {
                'date': date_match.group(1),
                'records': []
            }
            
            # Processa o restante da linha como primeiro registro do dia
            record_data = parse_record_line(line)
            if record_data:
                current_day['records'].append(record_data)
        
        # Se estamos em um dia atual, processa registros adicionais
        elif current_day and is_record_line(line):
            record_data = parse_record_line(line)
            if record_data:
                current_day['records'].append(record_data)
    
    # Adiciona o último dia processado
    if current_day:
        structured['days'].append(current_day)
    
    return structured

def extract_employee_info(line):
    """Extrai informações do colaborador"""
    # Exemplo: "Colaborador(a): Giovanna AAvila (Matrícula: 509880)"
    employee_match = re.match(r'Colaborador\(a\):\s*(.+?)\s*\(Matrícula:\s*(\d+)\)', line)
    if employee_match:
        return {
            'name': employee_match.group(1).strip(),
            'registration': employee_match.group(2).strip()
        }
    return {}

def extract_period_info(line):
    """Extrai informações do período"""
    # Exemplo: "Período: 01/08/2025 a 31/08/2025"
    period_match = re.match(r'Período:\s*(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}/\d{2}/\d{4})', line)
    if period_match:
        return {
            'start_date': period_match.group(1),
            'end_date': period_match.group(2),
            'month_year': '08/2025'  # Poderia extrair automaticamente
        }
    return {}

def is_record_line(line):
    """Verifica se a linha parece ser um registro de ponto"""
    # Ignora linhas que são claramente cabeçalhos ou títulos
    excluded_terms = ['Data', 'Ocorrência', 'Justificativa', 'Projetos', 'Ticket', 'Início', 'Saída', 'Inativo', 'Horas', 'Motivo']
    return not any(term in line for term in excluded_terms) and len(line) > 5

def parse_record_line(line):
    """Faz parsing de uma linha de registro de ponto"""
    # Divide a linha em partes baseado em múltiplos espaços
    parts = re.split(r'\s{2,}', line.strip())
    
    if not parts or len(parts) < 2:
        return None
    
    record = {
        'occurrence_type': parts[1] if len(parts) > 1 else '',
        'justification': parts[2] if len(parts) > 2 else '',
        'projects': parts[3] if len(parts) > 3 else '',
        'ticket': parts[4] if len(parts) > 4 else '',
        'start_time': parts[5] if len(parts) > 5 else '',
        'end_time': parts[6] if len(parts) > 6 else '',
        'inactive_time': parts[7] if len(parts) > 7 else '',
        'hours': parts[8] if len(parts) > 8 else '',
        'reason': parts[9] if len(parts) > 9 else ''
    }
    
    # Limpeza e processamento adicional
    record['is_compensated'] = 'Compensado' in record['occurrence_type']
    record['is_manual'] = 'Manual' in record['occurrence_type']
    record['is_overtime'] = 'extra' in record['occurrence_type'].lower()
    
    return record

def extract_header_info(text):
    """Extrai informações do cabeçalho"""
    header_info = {}
    
    # Empregado
    employee_match = re.search(r'Colaborador\(a\):\s*(.+?)\s*\(Matrícula:\s*(\d+)\)', text)
    if employee_match:
        header_info['employee'] = {
            'name': employee_match.group(1).strip(),
            'registration': employee_match.group(2).strip()
        }
    
    # Período
    period_match = re.search(r'Período:\s*(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}/\d{2}/\d{4})', text)
    if period_match:
        header_info['period'] = {
            'start': period_match.group(1),
            'end': period_match.group(2)
        }
    
    return header_info

def extract_period_summary(structured_data):
    """Extrai resumo do período"""
    days = structured_data.get('days', [])
    
    work_hours = 0
    overtime_hours = 0
    project_hours = 0
    
    for day in days:
        for record in day.get('records', []):
            if record.get('hours'):
                hours_str = record['hours']
                try:
                    hours = parse_hours_to_minutes(hours_str)
                    if record.get('is_overtime'):
                        overtime_hours += hours
                    elif 'Projeto' in record.get('occurrence_type', ''):
                        project_hours += hours
                    else:
                        work_hours += hours
                except:
                    pass
    
    return {
        'total_work_hours': format_minutes_to_hours(work_hours),
        'total_overtime_hours': format_minutes_to_hours(overtime_hours),
        'total_project_hours': format_minutes_to_hours(project_hours),
        'work_days_count': len([d for d in days if not all(r.get('is_compensated', False) for r in d.get('records', []))])
    }

def extract_daily_records(structured_data):
    """Extrai registros diários formatados"""
    daily_records = []
    
    for day in structured_data.get('days', []):
        day_record = {
            'date': day['date'],
            'is_compensated': all(r.get('is_compensated', False) for r in day.get('records', [])),
            'records': []
        }
        
        for record in day.get('records', []):
            day_record['records'].append({
                'occurrence_type': record.get('occurrence_type', ''),
                'justification': record.get('justification', ''),
                'projects': record.get('projects', ''),
                'ticket': record.get('ticket', ''),
                'start_time': record.get('start_time', ''),
                'end_time': record.get('end_time', ''),
                'inactive_time': record.get('inactive_time', ''),
                'hours': record.get('hours', ''),
                'reason': record.get('reason', ''),
                'is_manual_entry': record.get('is_manual', False),
                'is_overtime': record.get('is_overtime', False)
            })
        
        daily_records.append(day_record)
    
    return daily_records

def parse_hours_to_minutes(hours_str):
    """Converte string de horas (8:00) para minutos"""
    try:
        if ':' in hours_str:
            h, m = hours_str.split(':')
            return int(h) * 60 + int(m)
        else:
            return int(hours_str) * 60
    except:
        return 0

def format_minutes_to_hours(minutes):
    """Converte minutos para formato horas (H:MM)"""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}:{mins:02d}"

def count_total_records(structured_data):
    """Conta o total de registros"""
    return sum(len(day.get('records', [])) for day in structured_data.get('days', []))

def count_work_days(structured_data):
    """Conta dias de trabalho"""
    return len([day for day in structured_data.get('days', []) 
                if not all(r.get('is_compensated', False) for r in day.get('records', []))])

def count_compensated_days(structured_data):
    """Conta dias compensados"""
    return len([day for day in structured_data.get('days', []) 
                if all(r.get('is_compensated', False) for r in day.get('records', []))])