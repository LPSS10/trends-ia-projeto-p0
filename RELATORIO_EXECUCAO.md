# Relatório de Execução — Projeto P0: Analisador de Feedback para E-commerce

**Curso:** Capacitação em Desenvolvimento de Agentes de IA (TrendsIA — ResTIC / Softex Campinas)  
**Projeto:** P0 — Primeiro Fluxo com LLM  
**Local:** Salesópolis - São Paulo, (Home Office)  
**Data:** Novembro de 2026  
**Autor:** Luis Paulo da Silva de Siqueira (`lpaulo333gmailcom`)  
**Modelo e Provedor LLM:** `qwen3.5:9b-q4_K_M` via endpoint configurável (`LLM_HOST`, padrão `http://localhost:11434`)  
**Versão Entregue:** `p0-avancado`

---

## 1. Evolução por Nível

O projeto foi construído de forma incremental sobre a mesma base de código, consolidando as entregas em marcos versionados (*tags*):

* **Nível Básico (`p0-basico`):**
  * Implementação do núcleo funcional em Python (`src/client.py`) capaz de receber um texto de avaliação de cliente, formatar um prompt de análise e realizar uma chamada HTTP `POST` para a API do LLM (`qwen3.5:9b-q4_K_M`), exibindo a classificação de sentimento e um breve resumo.
  * Isolamento das configurações de acesso (URL do host, modelo e parâmetros) fora do código-fonte por meio de variáveis de ambiente (`python-dotenv`), declaração de dependências no `requirements.txt` e publicação inicial em repositório público no GitHub.

* **Nível Intermediário (`p0-intermediario`):**
  * Refatoração e separação clara de responsabilidades entre captura de entrada, carregamento de configuração, montagem do payload/prompt, chamada HTTP ao modelo, interpretação da resposta e apresentação ao usuário (incluindo interface web complementar em Flask em `src/app.py` e rota `/health`).
  * Implementação de validação para impedir o envio de entradas vazias e tratamento controlado de falhas previsíveis: configuração ausente ou inválida, credencial ausente/inválida (`401`), limite de requisições (`429`), indisponibilidade ou sobrecarga do gateway/servidor de inferência (`502`, `503`, `504`), falhas de conexão, *timeout* e respostas malformadas/vazias — sempre exibindo mensagens amigáveis sem expor *stack traces* ou segredos.
  * Criação do `.env.example` (sem credenciais reais), ajuste do `.gitignore` e organização do fluxo Git com *commits* atômicos e integração via *branch* e *Pull Request*.

* **Nível Avançado (`p0-avancado`):**
  * Externalização completa de parâmetros de geração (`LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `LLM_TIMEOUT`, `LLM_VERIFY_SSL`, `PORT`), permitindo ajustar o comportamento do modelo sem alterar o núcleo da aplicação.
  * Inclusão de registros de execução (*logging*) estruturados com métricas de latência e códigos de status HTTP, garantindo conformidade com a LGPD e segurança (sem registrar chaves, tokens ou dados sensíveis).
  * Criação da suíte de testes automatizados em `tests/test_client.py` (`pytest`) utilizando *mocks* para validar lógica local e cenários de erro sem depender de conexão externa, além da validação em ambiente limpo via novo ambiente virtual (`venv`) e conteinerização com `Dockerfile` / Gunicorn.

---

## 2. Decisões Principais

### Decisão 1: Uso de LLM para Classificação de Sentimento e Resumo
* **Decisão tomada:** Utilizar o modelo `qwen3.5:9b-q4_K_M` com prompt estruturado para classificar feedbacks em quatro categorias (`Positivo`, `Negativo`, `Neutro`, `Misto`) e gerar um resumo objetivo.
* **Alternativa considerada:** Regras fixas baseadas em palavras-chave (`if`/`else` em Python) ou análise léxica simples.
* **Justificativa:** Avaliações reais de e-commerce frequentemente contêm ironia, elogios acompanhados de ressalvas (sentimento `Misto`) ou relatos puramente factuais (`Neutro`). Regras fixas falham diante dessas nuances linguísticas, enquanto o LLM interpreta o contexto semântico e entrega simultaneamente a categoria e a síntese para priorização do atendimento.

### Decisão 2: Verificação SSL Configurável via Variável de Ambiente (`LLM_VERIFY_SSL`)
* **Decisão tomada:** Tornar a verificação de certificado SSL configurável via variável `LLM_VERIFY_SSL` e suprimir apenas os avisos redundantes de `urllib3` quando explicitamente desativada.
* **Alternativa considerada:** Manter `verify=True` fixo no `requests.post()` ou desabilitar SSL diretamente no código (*hardcoded*).
* **Justificativa:** Servidores com certificado autoassinado ou ambientes de teste específicos podem exigir `LLM_VERIFY_SSL=false` para evitar `SSLError`, enquanto ambientes de produção com certificado público válido podem manter `LLM_VERIFY_SSL=true`. Controlar isso por variável de ambiente dá flexibilidade sem fixar valores no código.

### Decisão 3: Timeout Estendido (`120.0s`) e Tratamento Explícito de HTTP `502`/`503`/`504`
* **Decisão tomada:** Configurar *timeout* padrão de `120` segundos nas chamadas ao LLM (e no servidor Gunicorn) e mapear especificamente erros de gateway/indisponibilidade (`502`, `503`, `504`) com mensagens orientativas ao usuário.
* **Alternativa considerada:** Manter o *timeout* curto padrão (`10s` ou `30s`) e tratar qualquer erro HTTP como falha genérica.
* **Justificativa:** Modelos carregados sob demanda (*cold start*) ou servidores ocupados podem levar até 1 ou 2 minutos para responder na primeira requisição. Um *timeout* curto interromperia requisições legítimas durante a inicialização, e mensagens específicas ajudam a distinguir indisponibilidade temporária do serviço de falhas de configuração.

### Decisão 4: Testes Automatizados com Simulação (`unittest.mock`) Separados dos Testes Reais
* **Decisão tomada:** Criar testes unitários em `tests/test_client.py` simulando respostas da API REST com `unittest.mock.patch`, mantendo a execução real documentada via CLI e interface Flask.
* **Alternativa considerada:** Realizar testes apenas por meio de chamadas reais ao endpoint remoto.
* **Justificativa:** Testes simulados garantem execução rápida, determinística e reproduzível por qualquer avaliador mesmo sem acesso a um servidor LLM ativo ou sem consumir recursos computacionais, além de permitirem validar cenários difíceis de reproduzir manualmente, como `401 Unauthorized` (credencial inválida), `429 Rate Limit` e `Timeout`.

---

## 3. Testes e Resultados

Os testes abaixo combinam **testes unitários simulados** (executados via `python -m pytest -v`) e **testes de integração** (executados via CLI e navegador com servidor LLM configurado):

| Teste | Tipo | Entrada ou Situação | Resultado Esperado | Resultado Obtido |
| :--- | :--- | :--- | :--- | :--- |
| **1. Feedback Positivo** | Integração (CLI / Web) | `"Entrega super rápida e produto de excelente qualidade!"` | Classificação `Positivo` e resumo coerente | **Sucesso:** Retornou `Sentimento: Positivo` e resumo destacando agilidade e qualidade. |
| **2. Feedback Negativo** | Integração (CLI / Web) | `"O aparelho parou de funcionar no segundo dia e ninguém responde o suporte."` | Classificação `Negativo` e resumo do problema | **Sucesso:** Retornou `Sentimento: Negativo` e resumo apontando defeito e falta de suporte. |
| **3. Feedback Misto** | Integração (CLI / Web) | `"Gostei muito do produto, mas a embalagem veio com manchas."` | Classificação `Misto` identificando elogio e ressalva | **Sucesso:** Retornou `Sentimento: Misto` e resumo equilibrando os dois pontos. |
| **4. Feedback Neutro** | Integração (CLI / Web) | `"O pacote foi deixado na portaria às 15h."` | Classificação `Neutro` para relato puramente factual | **Sucesso:** Retornou `Sentimento: Neutro` e resumo informativo sem polaridade. |
| **5. Entrada Vazia** | Integração / Simulado | String vazia `""` ou apenas espaços `"   "` | Impedir chamada ao LLM e orientar o usuário | **Sucesso:** Bloqueado antes da requisição com orientação para preencher o feedback. |
| **6. Credencial Ausente / Inválida** | Simulado (`pytest`) | `LLM_API_KEY` inválida retornando HTTP `401` ou ausência de configuração válida | Encerrar de forma controlada sem expor segredos | **Sucesso:** Exibiu mensagem amigável de erro de autenticação/configuração sem vazar chaves. |
| **7. Indisponibilidade (`502` / Cold Start)** | Integração / Simulado | Primeira chamada durante inicialização do modelo/serviço (`HTTP 502`) | Capturar erro `502` e informar indisponibilidade temporária | **Sucesso:** Retornou `"Serviço Indisponível (502): O gateway do LLM não respondeu a tempo."` sem quebrar a aplicação. |
| **8. Timeout / Falha de Rede** | Simulado (`pytest`) | Exceção `requests.exceptions.Timeout` ou `ConnectionError` | Tratar exceção de rede e orientar nova tentativa | **Sucesso:** Capturado de forma controlada com mensagem clara e registro de latência no log. |
| **9. Resposta Malformada** | Simulado (`pytest`) | JSON de retorno sem o campo esperado (`choices` / `message`) | Tratar formato inesperado sem *crash* | **Sucesso:** Retornou mensagem informando resposta inesperada do serviço de IA. |

---

## 4. Falhas e Limitações

### Falha 1: Erro HTTP 502 (Bad Gateway) na Primeira Requisição (*Cold Start* do Modelo)
* **O que aconteceu:** Ao testar uma frase factual (*"O pacote foi deixado na portaria às 15h."*) logo após iniciar o serviço/container, a aplicação retornou `"Serviço Indisponível (502): O gateway do LLM não respondeu a tempo."`.
* **Como foi identificado:** Observando o retorno controlado na interface da aplicação e acompanhando o comportamento do servidor de inferência durante o carregamento inicial do modelo.
* **Como foi tratado:** O tratamento específico de erros HTTP `502`/`503`/`504` e o `LLM_TIMEOUT=120.0` impediram que o servidor encerrasse com erro interno (`500`). Após aguardar o carregamento do modelo e reenviar o texto, a análise funcionou normalmente e retornou `Sentimento: Neutro`.
* **Por que permanece:** Trata-se de um comportamento de inicialização sob demanda do ambiente de inferência, fora do controle direto do código da aplicação.

### Falha 2: Classificação Ambígua em Frases Puramente Factuais
* **O que aconteceu:** Nos testes iniciais, frases sem carga emocional clara (como relatos de horário de entrega) tendiam a ser forçadas para `Positivo` ou `Negativo` pelo modelo.
* **Como foi identificado:** Durante a bateria de testes funcionais cobrindo diferentes perfis de mensagens de clientes.
* **Como foi tratado:** O prompt de sistema em `src/client.py` foi refinado para explicitar critérios objetivos diferenciando `Neutro` (relato factual sem elogio ou reclamação) de `Misto` (presença simultânea de pontos positivos e negativos).

### Limitações Conhecidas
* **Processamento unitário sem persistência:** A aplicação analisa um feedback por vez e não armazena histórico em banco de dados nem processa planilhas em lote (escopo deliberadamente mantido enxuto para o P0).
* **Dependência da disponibilidade do endpoint:** O usuário precisa apontar `LLM_HOST` para um servidor compatível com API REST / OpenAI API acessível a partir do ambiente de execução.

---

## 5. Uso de IA no Desenvolvimento

Durante o desenvolvimento do P0, ferramentas de IA generativa foram utilizadas como apoio técnico, sempre com revisão, testes locais e validação do autor:

* **Ferramenta utilizada:** Gemini (Google).
* **Tarefas delegadas:**
  1. Estruturação inicial da separação modular entre `src/client.py` (lógica de integração e tratamento de exceções) e `src/app.py` (rotas Flask e *healthcheck*).
  2. Refinamento das regras do prompt de sistema para melhorar a precisão na distinção entre feedbacks `Neutro` e `Misto`.
  3. Elaboração de casos de teste unitários com `unittest.mock` em `tests/test_client.py` para simular falhas HTTP (`401`, `429`, `502`, `Timeout`) sem chamadas reais.
  4. Revisão da estrutura da documentação (`README.md` e `RELATORIO_EXECUCAO.md`) para garantir reprodutibilidade em ambiente limpo.
* **Resultado aproveitado e alterações realizadas:** O esqueleto de tratamento de exceções e os *mocks* foram adaptados para refletir exatamente as variáveis de ambiente do projeto (`LLM_HOST`, `LLM_MODEL`, `LLM_VERIFY_SSL`, `LLM_TIMEOUT`), removendo referências específicas de ambiente interno e ajustando as mensagens de erro em português.
* **Forma de verificação:** Todos os trechos incorporados foram executados e validados localmente via `python -m pytest -v`, via linha de comando (CLI) e em container Docker.

---

## 6. Reflexão Final

* **Principal aprendizado:** Compreender na prática o ciclo completo de uma aplicação integrada a LLMs — indo além da chamada básica à API para incluir isolamento de dependências, proteção de configurações com `.env`, tratamento defensivo de falhas de rede/infraestrutura e documentação reproduzível.
* **Competência mais desenvolvida:** Integração robusta com APIs REST e diagnóstico de falhas em ambientes reais (`C03` e `C04`), especialmente ao lidar com certificados TLS/SSL, *cold start* de servidores de inferência e criação de testes automatizados com simulação.
* **Aspecto que ainda precisa ser aprimorado:** Evoluir a saída do modelo para formatos estruturados (como JSON validado com *schema*) e adicionar processamento em lote com métricas agregadas de sentimento, preparando a base para os próximos projetos do curso.