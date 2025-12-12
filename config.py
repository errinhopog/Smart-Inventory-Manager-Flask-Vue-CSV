import os
from dotenv import load_dotenv

# Carrega o .env antes de ler a classe Config
load_dotenv()

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    ALLOWED_EXTENSIONS = {'csv'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Configuração de Imagens
    # Mapeando para a pasta static/images como solicitado
    IMAGES_FOLDER = os.path.join(BASE_DIR, 'static', 'images')
    
    # Caminho do arquivo de dados
    DATA_FILE = os.path.join(UPLOAD_FOLDER, 'estoque_atual.csv')

    # Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY', 'chave-secreta-padrao-dev')
    # Tenta pegar a senha do ambiente, se não tiver, usa a padrão
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
