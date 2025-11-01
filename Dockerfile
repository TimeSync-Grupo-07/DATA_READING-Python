FROM python:3.11-slim

# Diretório de trabalho
WORKDIR /app

# Copia os arquivos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Executa o main
CMD ["python", "src/main.py"]
