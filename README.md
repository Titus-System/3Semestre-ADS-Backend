# InsightFlow - Backend

Backend do projeto **InsightFlow**, desenvolvido como projeto de integração das disciplinas de **Estrutura de Dados**, **Engenharia de Software II** e **Programação Orientada a Objetos**.

Esta API REST, implementada em **Python (Flask)**, fornece dados e estatísticas de desempenho do comércio exterior brasileiro, com foco em informações de **exportação e importação** dos anos de **2014 a 2024**, disponibilizadas pelo **Ministério do Desenvolvimento, Indústria, Comércio e Serviços (MDIC)**.

Através da API, é possível consultar dados e análises que identificam a performance de **estados**, **países** e **produtos** no comércio exterior brasileiro.

## 🛠️ Tecnologias utilizadas

<p align="center">
  <img alt="Python" height="30" width="40" src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg">
  <img alt="Flask" height="30" width="40" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/flask/flask-original.svg">
  <img alt="Pandas" height="30" width="40" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/pandas/pandas-original-wordmark.svg" />
  <img alt="PostgreSQL" height="30" width="40" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/postgresql/postgresql-original.svg">
  <img alt="Docker" height="30" width="40" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/docker/docker-plain.svg" />
  <img alt="Redis" height="30" width="40" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/redis/redis-original.svg">
  <img alt="AWS" height="30" width="40" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/amazonwebservices/amazonwebservices-plain-wordmark.svg" />
  <img alt="Git" height="30" width="40" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/git/git-original.svg">
  <img alt="GitHub" height="30" width="40" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/github/github-original.svg">
  <img alt="Jira" height="30" width="40" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/jira/jira-original.svg">
</p>

## 📊 Análise Estatística e Machine Learning
O InsightFlow Backend não apenas serve dados brutos, mas também realiza **análises estatísticas avançadas** e utiliza **técnicas de machine learning** para oferecer insights reais sobre o comércio exterior brasileiro.

- **[Statsmodels](https://www.statsmodels.org/)**: Utilizado para análises estatísticas robustas, como regressão linear, séries temporais e testes de hipóteses.
- **Pandas & NumPy**: Manipulação e estruturação de grandes volumes de dados.
- **Scikit-learn**: Aplicações de aprendizado de máquina para identificar padrões nos dados de exportação/importação.

### 🔍 Exemplos de análises realizadas

- **Cálculo do Índice de Herfindahl-Hirschman (HHI)** para medir a concentração de exportações por produto, município ou estado.
- **Comparações de desempenho anual e crescimento percentual** por categoria de produto.
- **Regressão Linear com Statsmodels** para avaliar correlações entre variáveis econômicas e volumes exportados.
- **Séries temporais e previsões** para detectar tendências de exportação em produtos estratégicos.

Essas análises são integradas diretamente às rotas da API, permitindo ao frontend consumir dados já processados, prontos para visualização em gráficos e dashboards interativos.

---

## 🚀 Como rodar o projeto

Siga os passos abaixo para configurar e executar o servidor corretamente:



### 1️⃣ Instalar e configurar o PostgreSQL

Acesse o documento abaixo para realizar a instalação e configuração do banco de dados:

📄 [`/docs/database/postgresql.md`](/docs/database/postgresql.md)

---

### 2️⃣ Preparar o ambiente virtual

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
````

#### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3️⃣ Instalar as dependências do projeto

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Configurar as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```env
DB_USER=usuario-banco-de-dados
DB_PASSWORD=senha-banco-de-dados
DB_HOST=host.docker.internal  # ou o IP/local onde seu PostgreSQL está rodando
DB_NAME=insightflow
DB_PORT=5432

BACKEND_SERVER=http://localhost:5000
FRONTEND_SERVER=http://localhost:5173

REDIS_HOST=host.docker.internal  # ou localhost, dependendo do seu setup
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

---

### 5️⃣ Executar a limpeza dos dados

Este passo prepara os dados brutos para inserção no banco.

#### Windows:

```bash
python tratar_dados.py
```

#### Linux/macOS:

```bash
python3 tratar_dados.py
```

---

### 6️⃣ Inicializar o banco de dados

Este comando carrega os dados limpos para o banco.
⚠️ **Pode levar horas dependendo do hardware. Aproximadamente 30 milhões de registros.**

```bash
python init_db.py
```

---

### 7️⃣ Iniciar o servidor Flask

#### Windows:

```bash
python run.py
```

#### Linux/macOS:

```bash
python3 run.py
```

---

## 🐳 Rodando com Docker (opcional)

### 📦 Build da imagem

```bash
docker build -t insightflow-backend .
```

### ▶️ Rodar o container

```bash
docker run --env-file .env -p 5000:5000 insightflow-backend
```

> Certifique-se de que o PostgreSQL e o Redis estejam rodando e acessíveis.

---

## 🧠 Redis (cache)

Este projeto utiliza **Redis** como sistema de cache para melhorar a performance das requisições e evitar recomputações pesadas.

### ▶️ Rodar Redis localmente com Docker

Se você tiver Docker instalado, é a forma mais simples de subir o Redis:

```bash
docker run -d --name redis-insightflow -p 6379:6379 redis
```

Isso iniciará um container com Redis acessível na porta padrão 6379.

---

### ▶️ Rodar Redis localmente sem Docker

#### Ubuntu/Debian:

```bash
sudo apt update
sudo apt install redis-server
```

Depois, inicie o serviço:

```bash
sudo service redis-server start
```

Você pode verificar se está rodando com:

```bash
redis-cli ping
```

Se retornar `PONG`, está tudo certo.

---

## 🐳 Executando rapidamente via Docker

Você pode rodar o projeto **InsightFlow - Backend** diretamente a partir da imagem hospedada no Docker Hub, sem precisar clonar o repositório ou instalar dependências.

---

### ✅ Pré-requisitos
- Docker instalado (acesse [https://www.docker.com](https://www.docker.com) para baixar)

### Passo 1: Baixe a imagem Docker do projeto
Use o comando abaixo para baixar a imagem publicada no Docker Hub:

```bash
docker pull pedrofsgarcia/insightflow-backend
```

### 📦 Passo 2: Crie o arquivo `.env`

Crie um arquivo `.env` na sua máquina, no mesmo diretório onde você executará o container, com o seguinte conteúdo:

```env
DB_USER=usuario-banco-de-dados
DB_PASSWORD=senha-banco-de-dados
DB_HOST=host.docker.internal  # ou o IP/local onde seu PostgreSQL está rodando
DB_NAME=insightflow
DB_PORT=5432

BACKEND_SERVER=http://localhost:5000
FRONTEND_SERVER=http://localhost:5173

REDIS_HOST=host.docker.internal  # ou localhost, dependendo do seu setup
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

### ▶️ Passo 3: Execute o container
```bash
docker run --env-file .env -p 5000:5000 pedrofsgarcia/insightflow-backend
```
- Usa as variáveis definidas no seu .env
- Expõe a porta 5000 da API na sua máquina


### 🔁 (Opcional) Rodar Redis local com Docker
Caso ainda não tenha o Redis rodando, execute:

```bash
docker run -d --name redis -p 6379:6379 redis
```

### 🚨 Observações importantes
Banco de Dados: Certifique-se de que o PostgreSQL esteja rodando e acessível via os parâmetros do .env.

Redis: Certifique-se também de que o Redis esteja rodando e acessível. Você pode rodá-lo via Docker:

```bash
docker run -d --name redis -p 6379:6379 redis
```
host.docker.internal: Funciona no Docker Desktop (Windows/macOS).
No Linux, substitua por localhost ou o IP da sua máquina.

🧪 Testar
Depois de rodar o container, acesse:

```arduino
http://localhost:5000
```
Você deverá ver a API Flask rodando.


## 👥 Contribuidores
Este backend foi desenvolvido por estudantes de Análise e Desenvolvimento de Sistemas com foco em Análise de dados como parte de uma plataforma de análise de dados aduaneiros. Mais informações sobre o projeto podem ser encontradas em [InsightFlow](https://github.com/Titus-System/InsightFlow).