import logging
import os

from flask import Flask, render_template_string, request

from src.client import analisar_feedback


def configurar_logs() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


configurar_logs()
app = Flask(__name__)

HTML_PAGE = """
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Analisador de Feedback (P0)</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 16px; background: #f8fafc; color: #0f172a; }
    .card { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
    h1 { margin-top: 0; font-size: 1.4rem; }
    textarea { width: 100%; min-height: 110px; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 1rem; box-sizing: border-box; }
    .actions { margin-top: 12px; display: flex; gap: 10px; }
    button { padding: 10px 18px; border: none; border-radius: 8px; font-size: 0.95rem; cursor: pointer; font-weight: 600; }
    .btn-primary { background: #2563eb; color: #fff; }
    .btn-secondary { background: #e2e8f0; color: #334155; text-decoration: none; display: inline-flex; align-items: center; padding: 10px 18px; border-radius: 8px; font-weight: 600; }
    .result { margin-top: 20px; padding: 16px; background: #f1f5f9; border-left: 4px solid #2563eb; border-radius: 6px; white-space: pre-wrap; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Analisador de Feedback (P0)</h1>
    <p>Insira o feedback abaixo para classificação e resumo via LLM.</p>
    <form method="post">
      <textarea name="feedback" placeholder="Ex.: Gostei muito do produto, chegou antes do prazo!" required>{{ feedback }}</textarea>
      <div class="actions">
        <button type="submit" class="btn-primary">Analisar Feedback</button>
        <a href="/" class="btn-secondary">Limpar</a>
      </div>
    </form>
    {% if resultado %}
    <div class="result">
      <strong>Resultado:</strong>
      <p style="margin: 10px 0 0 0;">{{ resultado }}</p>
    </div>
    {% endif %}
  </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    feedback = ""
    resultado = None
    if request.method == "POST":
        feedback = request.form.get("feedback", "")
        resultado = analisar_feedback(feedback)
    return render_template_string(HTML_PAGE, feedback=feedback, resultado=resultado)


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)