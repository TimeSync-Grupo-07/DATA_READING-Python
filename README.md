# Data Reader – Serviço de Extração de PDFs via E-mail e Envio para S3

Este serviço foi desenvolvido para realizar a leitura contínua de uma caixa de e-mail utilizando IMAP, identificar mensagens contendo arquivos PDF, extrair seu conteúdo, convertê-lo para JSON estruturado e armazenar o resultado em um bucket S3.

O container executa um loop contínuo de verificação, garantindo que novos e-mails sejam processados assim que chegarem.

## Funcionalidades

- Conexão IMAP para leitura da caixa de entrada.
- Extração automática de anexos PDF.
- Conversão dos PDFs para JSON estruturado.
- Geração de nome de arquivo baseado no colaborador presente no documento.
- Upload do JSON resultante para um bucket S3.
- Testes automáticos de permissão no S3 (listagem, upload e delete).
- Logs detalhados com timestamps.

## Arquitetura dos Arquivos

```text
/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.sample
└── src/
    ├── main.py
    ├── handlers/
    │   └── email_handler.py
    └── utils/
        └── pdf_to_json.py
```

## Pré-requisitos

Antes de rodar o serviço, você precisa ter:

### Infraestrutura

- Docker instalado
- Docker Compose instalado

### Permissões AWS

- Credenciais AWS configuradas na máquina.
- IAM com permissão mínima:
    
    - s3:ListBucket
    - s3:PutObject
    - s3:DeleteObject

### Permissões do serviço de e-mail

- Conta de e-mail compatível com IMAP.
- Caso use Gmail, é obrigatório utilizar uma senha de aplicativo.
- IMAP ativado nas configurações da conta.

## Configuração do Ambiente

Copie o arquivo ```.env.sample``` para ```.env```:

```bash
cp .env.sample .env
```

Edite o arquivo ```.env``` e preencha com suas credenciais:

```env
IMAP_HOST=imap.gmail.com
EMAIL_USER=seu_email@gmail.com
EMAIL_PASS=sua_senha_app
S3_BUCKET=seu-bucket
```

## Como Executar

### Subir o Container

```docker
docker compose up -d --build
```

### Ver Logs

```docker
docker logs -f data_reader
```

O container fará:

- Teste de permissão no S3.
- Conexão IMAP.
- Busca contínua por novos e-mails.
- Processamento de PDFs recebidos.
- Upload do JSON para o bucket.

## Como Funciona o Fluxo Interno

1. O ```main_loop()``` roda a cada 60 segundos.
2. ```fetch_new_pdfs()``` realiza a conexão IMAP e retorna PDFs novos.
3. Cada PDF é convertido via ```pdf_to_json()```.
4. O nome do arquivo no S3 é formatado com o nome do colaborador.
5. O upload é realizado com validação e tratamento de erros.
6. Logs exibem todos os passos, incluindo falhas e sucessos.

## Estrutura do JSON Gerado

O JSON gerado contém:

- metadata (versão, data de extração, páginas)
- header_info (colaborador, matrícula, período)
- period_summary (horas trabalhadas, extras, projeto)
- daily_records (lista estruturada por dia)
- raw_lines (conteúdo bruto extraído)
- processing_stats (totais e contagens)

