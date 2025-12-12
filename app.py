from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session
import os
import datetime
import shutil
from werkzeug.utils import secure_filename
from config import Config
from processor import StockProcessor
from functools import wraps
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Garante que as pastas existam
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['IMAGES_FOLDER'], exist_ok=True)

# Instância do processador
processor = StockProcessor(app.config['DATA_FILE'], app.config['IMAGES_FOLDER'])

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'error': 'Acesso não autorizado'}), 401
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'password' not in data:
        return jsonify({'success': False, 'message': 'Senha não fornecida'}), 400
    
    if data['password'] == app.config['ADMIN_PASSWORD']:
        session['logged_in'] = True
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Senha incorreta'}), 401

@app.route('/api/check-auth')
def check_auth():
    return jsonify({'authenticated': session.get('logged_in', False)})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/produtos')
@login_required
def get_produtos():
    try:
        produtos = processor.process()
        stats = processor.get_stats(produtos)
        
        data_atual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        if os.path.exists(app.config['DATA_FILE']):
            timestamp = os.path.getmtime(app.config['DATA_FILE'])
            data_atual = datetime.datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")
            
        return jsonify({
            'produtos': produtos,
            'stats': stats,
            'ultima_atualizacao': data_atual
        })
    except Exception as e:
        print(f"Erro crítico na API: {e}")
        return jsonify({'error': 'Erro ao processar dados do estoque', 'details': str(e)}), 500

@app.route('/api/historico/<sku>')
@login_required
def get_historico(sku):
    try:
        history = processor.get_product_history(sku)
        return jsonify(history)
    except Exception as e:
        return jsonify([])

@app.route('/api/dashboard')
@login_required
def get_dashboard():
    try:
        produtos = processor.process()
        stats = processor.get_dashboard_stats(produtos)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-image/<sku>', methods=['POST'])
@login_required
def upload_image(sku):
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhuma imagem enviada'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
        
    if file:
        # Salva como SKU.jpg
        filename = f"{sku}.jpg"
        filepath = os.path.join(app.config['IMAGES_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'success': True, 'message': 'Imagem atualizada com sucesso!'})
        
    return jsonify({'success': False, 'message': 'Erro ao salvar imagem'}), 400

@app.route('/print/reposicao')
@login_required
def print_reposicao():
    try:
        produtos = processor.process()
        # Filtra produtos com estoque baixo (<= 3) ou zerado
        # Convertendo para int para garantir
        def get_stock(p):
            try: return float(p.get('Stock', 0))
            except: return 0
            
        reposicao = [p for p in produtos if get_stock(p) <= 3]
        # Ordena por fornecedor/categoria se possível, ou nome
        reposicao.sort(key=lambda x: (x.get('Categories', ''), x.get('Name', '')))
        
        return render_template('print_reposicao.html', produtos=reposicao, date=datetime.datetime.now())
    except Exception as e:
        return f"Erro ao gerar relatório: {e}", 500

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
        
    if file and allowed_file(file.filename):
        # Backup automático
        if os.path.exists(app.config['DATA_FILE']):
            try:
                backup_dir = os.path.join(app.config['BASE_DIR'], 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                backup_path = os.path.join(backup_dir, f'estoque_{timestamp}.csv')
                shutil.copy2(app.config['DATA_FILE'], backup_path)
                print(f"Backup criado em: {backup_path}")
            except Exception as e:
                print(f"Erro ao criar backup: {e}")

        file.save(app.config['DATA_FILE'])
        return jsonify({'success': True, 'message': 'Estoque atualizado com sucesso!'})
    
    return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido. Use CSV.'}), 400

@app.route('/imagens/<path:filename>')
def serve_image(filename):
    return send_from_directory(app.config['IMAGES_FOLDER'], filename)

if __name__ == '__main__':
    print("🚀 Servidor AquaFlora Estoque rodando!")
    print("👉 Acesse localmente: http://127.0.0.1:8000")
    print("👉 Acesse na rede: http://0.0.0.0:8000 (Use o IP do computador)")
    # host='0.0.0.0' permite que outros computadores na rede acessem o sistema
    app.run(host='0.0.0.0', debug=True, port=8000)
