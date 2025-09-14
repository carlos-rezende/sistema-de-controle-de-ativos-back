from flask import Flask
from flask_cors import CORS

# Cria a aplicação Flask
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return {
        "message": "Sistema de Controle de Ativos API",
        "version": "1.0.0",
        "status": "online",
        "note": "Esta é uma versão adaptada para Flask. Para funcionalidade completa, use a versão FastAPI original."
    }

@app.route('/health')
def health():
    return {"status": "healthy"}

@app.route('/api/info')
def api_info():
    return {
        "endpoints": [
            "GET / - Informações da API",
            "GET /health - Status de saúde",
            "GET /api/info - Informações dos endpoints"
        ],
        "original_features": [
            "Gestão completa de ativos financeiros",
            "Integração com API brapi.dev",
            "Análises de performance e risco",
            "Gestão de carteiras",
            "Histórico de cotações e dividendos"
        ],
        "note": "Para acessar todas as funcionalidades, execute a versão FastAPI localmente"
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

