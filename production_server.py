from app import app
from waitress import serve

if __name__ == "__main__":
    print("🚀 Servidor de Produção AquaFlora Rodando!")
    print("👉 Aguardando conexões na porta 8000...")
    serve(app, host='0.0.0.0', port=8000)