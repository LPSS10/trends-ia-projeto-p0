# Analisador de Feedback (P0) — Trends IA

Aplicação desenvolvida em **Python** e **Flask** (servida em produção com **Gunicorn** na porta `8000`) que utiliza um modelo de linguagem (LLM) para analisar avaliações de clientes de e-commerce, classificando o sentimento (**Positivo**, **Negativo**, **Neutro** ou **Misto**) e gerando um resumo curto e objetivo.

## Sumário

 1. [O que este projeto faz](#o-que-este-projeto-faz)

 2. [Público-alvo, justificativa e limites](#público-alvo-justificativa-e-limites)

 3. [Pré-requisitos](#pré-requisitos)

 4. [Estrutura do Projeto](#estrutura-do-projeto)

 5. [Passo 1: Baixar o projeto do GitHub](#passo-1-baixar-o-projeto-do-github)

 6. [Passo 2: Preparar o ambiente Python](#passo-2-preparar-o-ambiente-python)

 7. [Passo 3: Configurar as variáveis de ambiente (.env)](#passo-3-configurar-as-variáveis-de-ambiente-env)

 8. [Passo 4: Como testar pelo Terminal (CLI) e Testes Automatizados](#passo-4-como-testar-pelo-terminal-cli-e-testes-automatizados)

 9. [Passo 5: Como testar pelo Navegador (Python + Flask)](#passo-5-como-testar-pelo-navegador-python--flask)

10. [Passo 6: Executar e empacotar via Docker](#passo-6-executar-e-empacotar-via-docker)

11. [Limitações Conhecidas](#limitações-conhecidas)

12. [Solução de Problemas Comuns](#solução-de-problemas-comuns)

13. [Vídeo de Demonstração](#vídeo-de-demonstração)

## O que este projeto faz

Quando você insere o texto de um feedback de cliente (seja pelo terminal ou pela página web), a aplicação:

1. **Valida a entrada:** Verifica se o texto não está vazio.

2. **Envia para o LLM:** Formata um prompt estruturado com regras claras de classificação e envia via requisição HTTP (`POST /v1/chat/completions`) para o modelo configurado (padrão: `qwen3.5:9b-q4_K_M`).

3. **Retorna o resultado:** Exibe o sentimento identificado (`Positivo`, `Negativo`, `Neutro` ou `Misto`) acompanhado de um resumo em 1 ou 2 frases.

4. **Trata falhas de rede/servidor:** Caso o serviço de IA demore a responder, retorne erro (`401`, `429`, `502`, `503`, `504`) ou fique fora do ar, o sistema exibe uma mensagem amigável sem travar a aplicação.

## Público-alvo, justificativa e limites

* **Público-alvo:** Equipes de atendimento ao cliente e suporte de e-commerce que precisam triar avaliações e mensagens diariamente com mais agilidade.

* **Por que usar um LLM:** Regras fixas com condicionais simples (`if`/`else`) têm dificuldade para interpretar nuances da linguagem humana, como ironia, sarcasmo, tom emocional e feedbacks mistos. Um LLM interpreta o contexto semântico para classificar o sentimento e sintetizar o ponto principal do relato.

* **Limites do projeto:** O P0 tem escopo reduzido e focado: integra um único LLM via API REST com configuração por variáveis de ambiente e testes automatizados. Não inclui autenticação de usuários, banco de dados persistente, RAG ou múltiplos agentes.

## Pré-requisitos

Antes de começar, certifique-se de ter instalado no seu computador:

* **Git:** Para baixar o código do GitHub ([baixar Git](https://git-scm.com/downloads)).

* **Python 3.10 ou superior** (recomendado **Python 3.12**): Para executar a aplicação e os testes ([baixar Python](https://www.python.org/downloads/)).

  > **Dica no Windows:** Durante a instalação do Python, marque a opção **"Add Python to PATH"**.

* **Acesso a um servidor LLM compatível com API REST / OpenAI-compatible** (como um servidor local via **Ollama** ou endpoint configurado via variável de ambiente) para realizar análises reais. *(Os testes automatizados com `pytest` funcionam mesmo sem acesso ao servidor LLM).*

* **Docker** *(opcional)*: Necessário apenas se quiser construir a imagem ou exportar o arquivo `.tar`.

## Estrutura do Projeto

```text
trends-ia-projeto-p0/
├── src/
│   ├── __init__.py       # Inicializa o pacote Python
│   ├── app.py            # Servidor web Flask (rotas "/" e "/health")
│   └── client.py         # Comunicação com a API do LLM, prompts e tratamento de erros
├── tests/
│   ├── __init__.py       # Inicializa o pacote de testes
│   └── test_client.py    # Testes automatizados (pytest)
├── .env.example          # Modelo de configuração das variáveis de ambiente
├── .gitignore            # Arquivos ignorados pelo Git (venv, .env, .tar, etc.)
├── Dockerfile            # Receita para construir a imagem Docker com Gunicorn
├── RELATORIO_EXECUCAO.md # Relatório técnico de execução e validação do P0
├── requirements.txt      # Lista de bibliotecas Python necessárias
└── README.md             # Este guia de instruções
```

## Passo 1: Baixar o projeto do GitHub

Abra o terminal do seu sistema operacional:

* **Windows:** Abra o PowerShell ou o Prompt de Comando (CMD).

* **Linux / macOS:** Abra o Terminal.

Navegue até a pasta onde deseja salvar o projeto (por exemplo, Documentos ou Desktop) e execute o comando abaixo para clonar o repositório:

```bash
git clone https://github.com/LPSS10/trends-ia-projeto-p0.git
cd trends-ia-projeto-p0
```

## Passo 2: Preparar o ambiente Python

Criar um ambiente virtual (`venv`) isola as bibliotecas deste projeto para não interferir em outros programas do seu computador.

**No Windows (PowerShell):**

```bash
# 1. Cria o ambiente virtual
python -m venv venv

# 2. Ativa o ambiente virtual
.\venv\Scripts\Activate.ps1

# 3. Instala todas as dependências do projeto
pip install -r requirements.txt
```

> **Caso o PowerShell bloqueie a ativação do venv:** Rode o comando `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`, confirme com `S` e tente ativar novamente.

**No Linux ou macOS:**

```bash
# 1. Cria o ambiente virtual
python3 -m venv venv

# 2. Ativa o ambiente virtual
source venv/bin/activate

# 3. Instala todas as dependências do projeto
pip install -r requirements.txt
```

Quando o ambiente estiver ativo, você verá `(venv)` no início da linha do terminal.

## Passo 3: Configurar as variáveis de ambiente (.env)

A aplicação usa um arquivo oculto chamado `.env` para carregar o endereço do serviço de IA, o modelo e os parâmetros de execução. **Nunca** versione o arquivo `.env` nem chaves ou credenciais reais no GitHub.

> **Sobre chave de API (`LLM_API_KEY`):** Se o servidor escolhido não exigir autenticação, você não precisa configurar chave de API. Caso o seu provedor exija token/chave, adicione `LLM_API_KEY=sua_chave_aqui` no `.env` (nunca no código nem no Git).

Copie o arquivo de exemplo `.env.example` criando o arquivo `.env`:

**Windows (PowerShell):**

```bash
Copy-Item .env.example .env
```

**Linux / macOS:**

```bash
cp .env.example .env
```

Abra o arquivo `.env` no VS Code (ou em outro editor de texto) e preencha os valores conforme o seu ambiente de execução:

```env
LLM_HOST=http://localhost:11434
LLM_MODEL=qwen3.5:9b-q4_K_M
LLM_VERIFY_SSL=true
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=1024
LLM_TIMEOUT=120.0
PORT=8000
```

### Variáveis e seus significados

| Variável | O que significa | 
| ----- | ----- | 
| `LLM_HOST` | Endereço base do servidor de IA (ex.: `http://localhost:11434` com Ollama local ou o endpoint configurado no seu ambiente). | 
| `LLM_MODEL` | Nome do modelo de IA carregado no servidor. | 
| `LLM_VERIFY_SSL` | Use `true` para validar certificado HTTPS público ou `false` apenas quando necessário em ambiente com certificado autoassinado. | 
| `LLM_TEMPERATURE` | Controla a variação/criatividade da resposta (`0.3` mantém as respostas mais consistentes). | 
| `LLM_MAX_TOKENS` | Tamanho máximo (em tokens) da resposta gerada pelo modelo. | 
| `LLM_TIMEOUT` | Tempo máximo de espera (em segundos) pela resposta do servidor de IA. | 
| `PORT` | Porta local onde o servidor Flask será aberto (padrão `8000`). | 

## Passo 4: Como testar pelo Terminal (CLI) e Testes Automatizados

Você pode validar o projeto diretamente pela linha de comando de duas formas:

### A) Testes simulados (sem chamada real ao LLM)

Este teste executa a suíte automatizada com dublês (*mocks*) para verificar a montagem do prompt, leitura das variáveis e tratamento de erros sem precisar de conexão com o servidor de IA:

```bash
python -m pytest -v
```

**Resultado esperado:** Todos os testes devem aparecer com o status `PASSED` em verde.

### B) Testes reais via CLI (com servidor LLM acessível)

Com o servidor LLM acessível no endereço configurado em `LLM_HOST`, você pode chamar a função `analisar_feedback` direto pelo terminal sem abrir o navegador:

```bash
python -c "from src.client import analisar_feedback; print(analisar_feedback('Gostei muito do produto, mas a embalagem veio com manchas.'))"
python -c "from src.client import analisar_feedback; print(analisar_feedback('Entrega super rápida e produto de excelente qualidade!'))"
python -c "from src.client import analisar_feedback; print(analisar_feedback('O aparelho parou de funcionar no segundo dia e ninguém responde o suporte.'))"
python -c "from src.client import analisar_feedback; print(analisar_feedback('O pacote foi deixado na portaria às 15h.'))"
```

**Saída esperada no terminal:**

```text
Sentimento: Misto
Resumo: O cliente elogiou o produto, mas relatou insatisfação com manchas na embalagem.
```

## Passo 5: Como testar pelo Navegador (Python + Flask)

Para usar a interface gráfica completa no navegador:

1. Com o ambiente `(venv)` ativado na raiz do projeto, inicie o servidor web Flask:

   ```bash
   python -m src.app
   ```

   O terminal mostrará que o servidor está rodando na porta `8000` (ex.: `Running on http://0.0.0.0:8000`). Esse terminal ficará ocupado enquanto o servidor estiver rodando — se quiser rodar outros comandos enquanto ele está ativo, abra um segundo terminal e ative o `venv` nele também.

2. Abra seu navegador de preferência (Chrome, Edge, Firefox) e acesse:

   * **Aplicação Principal:** `http://localhost:8000`

   * **Verificação de Saúde (Healthcheck):** `http://localhost:8000/health` (deve retornar `{"status": "ok"}`)

3. **Como usar a tela web:**

   * Digite ou cole o comentário de um cliente na caixa de texto.

   * Clique no botão **Analisar Feedback**.

   * Aguarde alguns segundos enquanto o modelo processa o texto.

   * O **Sentimento** e o **Resumo** aparecerão logo abaixo na seção **Resultado**.

   * Clique em **Limpar** para apagar o texto e fazer um novo teste.

4. Para encerrar o servidor quando terminar, volte ao terminal onde o Flask está rodando e pressione `Ctrl + C`.

## Passo 6: Executar e empacotar via Docker

Se você possui o Docker instalado e deseja construir a imagem, validar os testes dentro do container ou exportar o arquivo `.tar`:

```bash
docker build -t lpaulo333gmailcom:latest .
docker run --rm lpaulo333gmailcom:latest python -m pytest -v
docker images lpaulo333gmailcom:latest
docker save --output lpaulo333gmailcom.tar lpaulo333gmailcom:latest
```

**Testar o container localmente (opcional):**

```bash
docker run --rm -p 8000:8000 --env-file .env lpaulo333gmailcom:latest
```

Depois acesse `http://localhost:8000` no navegador.

## Limitações Conhecidas

* **Dependência do modelo e do contexto:** A precisão da classificação (especialmente em ironias muito sutis) depende do modelo configurado no servidor LLM.

* **Cold start do servidor de inferência:** Servidores de GPU sob demanda podem levar de 1 a 2 minutos na primeira requisição após inatividade, exigindo `LLM_TIMEOUT` adequado.

* **Escopo unitário:** A aplicação processa um feedback por vez e não armazena histórico em banco de dados nem realiza autenticação de usuários.

## Solução de Problemas Comuns

* **Erro de Rede: Não foi possível conectar ao serviço de LLM**

  * Verifique se o endereço `LLM_HOST` no arquivo `.env` está correto, se o servidor LLM está em execução e se há conectividade de rede até ele.

* **Serviço Indisponível (502 / 503 / 504) ou Timeout**

  * Indica sobrecarga momentânea ou carregamento inicial do modelo no servidor de IA (*cold start*). Aguarde alguns instantes e envie o feedback novamente.

* **`ModuleNotFoundError: No module named 'src'`**

  * Certifique-se de estar na pasta raiz (`trends-ia-projeto-p0`) e execute sempre usando `-m` (`python -m src.app` ou `python -m pytest -v`).

* **Porta `8000` já está em uso**

  * Altere `PORT=8001` no arquivo `.env` e acesse `http://localhost:8001` no navegador.

## Vídeo de Demonstração

* **Link (YouTube — não listado, até 5 minutos):** `https://youtu.be/SEU_LINK_AQUI`