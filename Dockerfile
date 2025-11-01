FROM python:3.11-slim

# Configurações de encoding mais robustas
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV LANGUAGE=C.UTF-8

WORKDIR /app

# Instala dependências do sistema para suporte a encoding
RUN apt-get update && apt-get install -y \
    locales \
    && rm -rf /var/lib/apt/lists/* \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8

# Copia e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código
COPY . .

# Adiciona o diretório raiz ao PYTHONPATH
ENV PYTHONPATH=/app

CMD ["python", "src/main.py"]