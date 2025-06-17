# Dockerfile
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia todos os arquivos para dentro do container
COPY . .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta usada pela aplicação
EXPOSE 5000

# Comando para rodar o Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
