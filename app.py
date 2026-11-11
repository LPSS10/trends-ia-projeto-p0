
import os
import urllib3
import requests
from flask import Flask, render_template_string, request


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

LLM_HOST = os.getenv("OLLAMA_HOST", "https://llm-internal.softex:9001")
LLM_API_URL = f"{LLM_HOST}/api/generate"

# HTML simples para interface de teste do analisador de feedback sei que não é obrigatorio mas é bom ter uma interface para testar a aplicação.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Analisador de Feedback - P0</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f4f4f9; color: #333; }
        .container { max-width: 600px; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        textarea { width: 100%; height: 100px; padding: 10px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .result { margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 4px; white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Analisador de Feedback para E-commerce</h2>
        <form method="POST">
        # A minha ideia para P0 é que os dados dos clientes sejam chamados de um banco de dodos para analise, imediata processandos e encaminhados para outro banco de dados, mas para verificações iniciais das demandas dos clientes, esse passoa poderam ser desenvolvido aqui no curso se eu tiver oportunidade mais adiante.
            <label for="feedback">Insira o feedback do cliente:</label><br>
            <textarea name="feedback" placeholder="Ex: O produto chegou rápido, mas veio com defeito na embalagem.">{{ feedback or '' }}</textarea>
            <button type="submit">Analisar com LLM</button>
        </form>
        {% if resultado %}
            <div class="result">
                <strong>Resultado da Análise:</strong><br>
                {{ resultado }}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
  resultado = None
  feedback = ""
  if request.method == "POST":
    feedback = request.form.get("feedback", "")
    if feedback.strip():
      prompt = (
          "Analise o seguinte feedback de e-commerce:\n"
          f'"{feedback}"\n\n'
          "Forneça:\n"
          "1. Classificação (Positivo ou Negativo)\n"
          "2. Resumo/Extração dos pontos principais do texto curto."
      )

      payload = {
          "model": "qwen2.5", 
          "prompt": prompt,
          "stream": False,
      }

      try:
        response = requests.post(
            LLM_API_URL, json=payload, verify=False, timeout=30
        )
        if response.status_code == 200:
          data = response.json()
          resultado = data.get(
              "response", "Resposta vazia retornada pela LLM."
          )
        else:
          resultado = f"Erro na API da LLM: Código {response.status_code}"
      except Exception as e:
        resultado = f"Erro de conexão com a LLM interna: {str(e)}"

  return render_template_string(
      HTML_TEMPLATE, resultado=resultado, feedback=feedback
  )


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 80))
  app.run(host="0.0.0.0", port=port)