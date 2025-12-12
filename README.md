# 🌿 AquaFlora Estoque

Sistema de gerenciamento de estoque simples e eficiente, desenvolvido para controle de produtos, preços e reposição.

## ✨ Funcionalidades

*   **Controle de Estoque**: Visualização clara de produtos, quantidades e preços.
*   **Dashboard Gerencial**: Visão geral com valor total em estoque, itens críticos e top categorias.
*   **Upload de Imagens**: Adicione fotos aos produtos diretamente pelo sistema.
*   **Relatório de Reposição**: Gere e imprima listas de produtos com estoque baixo para conferência.
*   **Histórico de Preços**: Acompanhe a evolução dos preços de cada produto.
*   **Temas Personalizáveis**: Escolha entre modo claro, escuro e temas coloridos.
*   **Segurança**: Autenticação protegida no servidor.

## 🚀 Como Rodar

### Pré-requisitos

*   Python 3.8 ou superior
*   Pip (Gerenciador de pacotes do Python)

### Instalação

1.  Clone o repositório ou baixe os arquivos.
2.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

### Executando

1.  Inicie o servidor:
    ```bash
    python app.py
    ```
    Ou execute o arquivo `iniciar_site.bat` (no Windows).

2.  Acesse no navegador:
    *   Local: `http://127.0.0.1:8000`
    *   Rede: `http://SEU_IP:8000`

## 🔒 Acesso

O sistema é protegido por senha.
*   **Senha**: Configurada via variável de ambiente ou no arquivo `.env` com "ADMIN_PASSWORD=".

## 🛠️ Estrutura do Projeto

*   `app.py`: Servidor principal (Flask).
*   `processor.py`: Lógica de processamento de dados e CSV.
*   `config.py`: Configurações do sistema.
*   `templates/`: Arquivos HTML.
*   `static/`: Arquivos CSS, JS e Imagens.
*   `uploads/`: Onde o arquivo CSV do estoque é armazenado.

## 📦 Deploy

Para colocar online (Hostinger, AWS, etc.), recomenda-se usar Gunicorn ou Waitress como servidor de produção e configurar um proxy reverso (Nginx).

---
Desenvolvido para AquaFlora.
