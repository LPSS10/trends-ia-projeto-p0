import os
import traceback
import urllib3
import requests
from flask import Flask, render_template_string, request

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

LLM_HOST = os.getenv("OLLAMA_HOST", "https://llm-internal.softex:9001")
LLM_API_URL = f"{LLM_HOST}/v1/chat/completions"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Analisador de Feedback - P0</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f4f4f9; color: #333; }
        .container { max-width: 600px; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        textarea { width: 100%; height: 120px; padding: 10px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; resize: vertical; box-sizing: border-box; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .result { margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 4px; white-space: pre-wrap; font-family: monospace; font-size: 13px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Analisador de Feedback para E-commerce</h2>
        <form method="POST">
            <label for="feedback">Insira o feedback do cliente:</label><br>
            <textarea name="feedback" placeholder="Digite o feedback aqui!">{{ feedback or '' }}</textarea><br>
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

            model_name = os.getenv("LLM_MODEL", "qwen3.5:9b-q4_K_M")
            
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }

            try:
                response = requests.post(
                    LLM_API_URL, json=payload, verify=False, timeout=120
                )
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices")
                    if choices and len(choices) > 0:
                        resultado = choices[0].get("message", {}).get("content", "Conteúdo da mensagem vazio.")
                    else:
                        resultado = f"Resposta JSON inesperada da LLM: {data}"
                else:
                    resultado = f"Erro na API da LLM: Código {response.status_code} - {response.text}"
            except Exception as e:
                resultado = f"Erro interno capturado:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"

    return render_template_string(
        HTML_TEMPLATE, resultado=resultado, feedback=feedback
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    app.run(host="0.0.0.0", port=port)