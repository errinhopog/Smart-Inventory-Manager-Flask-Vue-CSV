const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'], // Use [[ ]] to avoid conflict with Jinja2
    data() {
        return {
            products: [],
            lastUpdate: '',
            loading: true,
            search: '',
            selectedCategory: '',
            currentPage: 1,
            itemsPerPage: 24,
            isDark: false,
            showMobileFilters: false,
            showUploadModal: false,
            showThemeMenu: false,
            currentTheme: 'aqua',
            themes: {
                aqua: { 
                    name: 'AquaFlora (Claro)', 
                    colors: { 
                        primary: '#10B981', 
                        secondary: '#0ea5e9', 
                        bg: '#f3f4f6', 
                        text: '#1f2937', 
                        card: '#ffffff', 
                        border: '#e5e7eb',
                        headerBg: '#111827',
                        headerText: '#ffffff'
                    } 
                },
                dark: { 
                    name: 'Modo Escuro', 
                    colors: { 
                        primary: '#34d399', 
                        secondary: '#38bdf8', 
                        bg: '#0f172a', 
                        text: '#f1f5f9', 
                        card: '#1e293b', 
                        border: '#334155',
                        headerBg: '#1e293b',
                        headerText: '#f1f5f9'
                    } 
                },
                midnight: { 
                    name: 'Midnight Blue', 
                    colors: { 
                        primary: '#60a5fa', 
                        secondary: '#a78bfa', 
                        bg: '#020617', 
                        text: '#f8fafc', 
                        card: '#1e293b', 
                        border: '#1e3a8a',
                        headerBg: '#172554',
                        headerText: '#f8fafc'
                    } 
                },
                forest: { 
                    name: 'Floresta Noturna', 
                    colors: { 
                        primary: '#4ade80', 
                        secondary: '#facc15', 
                        bg: '#052e16', 
                        text: '#ecfdf5', 
                        card: '#064e3b', 
                        border: '#065f46',
                        headerBg: '#022c22',
                        headerText: '#ecfdf5'
                    } 
                },
                contrast: { 
                    name: 'Alto Contraste', 
                    colors: { 
                        primary: '#fbbf24', 
                        secondary: '#ffffff', 
                        bg: '#000000', 
                        text: '#ffffff', 
                        card: '#000000', 
                        border: '#ffffff',
                        headerBg: '#000000',
                        headerText: '#fbbf24'
                    } 
                }
            },
            selectedFile: null,
            uploading: false,
            isAuthenticated: false,
            password: '',
            showScanner: false,
            html5QrCode: null,
            cameras: [],
            currentCameraIndex: 0,
            onlyLowStock: false,
            selectedProduct: null,
            
            // New Features
            showProductModal: false,
            priceHistory: [],
            
            // Dashboard
            showDashboardModal: false,
            dashboardStats: {},

            // Bulk Selection
            selectedItems: [],
            
            // Conference Mode
            showConferenceModal: false,
            isConferenceMode: false,
            conferenceItems: [],
        }
    },
    computed: {
        categories() {
            const cats = new Set(this.products.map(p => p.Categories).filter(Boolean));
            return Array.from(cats).sort();
        },
        filteredProducts() {
            // Products are already sorted by image existence from backend
            let result = this.products;
            
            if (this.onlyLowStock) {
                result = result.filter(p => Number(p.Stock) <= 3);
            }

            if (this.selectedCategory) {
                result = result.filter(p => p.Categories === this.selectedCategory);
            }
            
            if (this.search) {
                const term = this.search.toLowerCase();
                // Fuzzy-ish search: split terms and check if all exist
                const terms = term.split(/\s+/).filter(t => t.length > 0);
                
                result = result.filter(p => {
                    const searchStr = `${p.Name} ${p.SKU} ${p['Meta: _marca'] || ''}`.toLowerCase();
                    return terms.every(t => searchStr.includes(t));
                });
            }
            
            return result;
        },
        totalPages() {
            return Math.ceil(this.filteredProducts.length / this.itemsPerPage);
        },
        paginatedProducts() {
            const start = (this.currentPage - 1) * this.itemsPerPage;
            const end = start + this.itemsPerPage;
            return this.filteredProducts.slice(start, end);
        },
        allSelected() {
            return this.paginatedProducts.length > 0 && this.paginatedProducts.every(p => this.selectedItems.includes(p.SKU));
        },
        inStockCount() {
            return this.filteredProducts.filter(p => Number(p.Stock) > 0).length;
        },
        outOfStockCount() {
            return this.filteredProducts.filter(p => Number(p.Stock) <= 0).length;
        }
    },
    watch: {
        search() { this.currentPage = 1; },
        selectedCategory() { this.currentPage = 1; },
        isDark(newVal) {
            if (newVal) document.documentElement.classList.add('dark');
            else document.documentElement.classList.remove('dark');
            localStorage.setItem('darkMode', newVal);
        },
        themeColor(newVal) {
            this.updateThemeColor(newVal);
        }
    },
    mounted() {
        this.loadTheme();
        this.checkAuth();
    },
    methods: {
        async checkAuth() {
            try {
                const response = await fetch('/api/check-auth');
                const data = await response.json();
                this.isAuthenticated = data.authenticated;
                if (this.isAuthenticated) {
                    this.fetchData();
                }
            } catch (e) {
                this.isAuthenticated = false;
            }
        },
        async login() {
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password: this.password })
                });
                const data = await response.json();
                
                if (data.success) {
                    this.isAuthenticated = true;
                    this.fetchData();
                    Swal.fire({
                        title: 'Bem-vindo!',
                        text: 'Login realizado com sucesso.',
                        icon: 'success',
                        timer: 1500,
                        showConfirmButton: false
                    });
                } else {
                    Swal.fire('Acesso Negado', data.message || 'Senha incorreta.', 'error');
                }
            } catch (error) {
                Swal.fire('Erro', 'Erro ao conectar com o servidor.', 'error');
            }
        },
        async logout() {
            try {
                await fetch('/api/logout', { method: 'POST' });
                this.isAuthenticated = false;
                this.products = [];
            } catch (error) {
                console.error('Erro ao sair:', error);
            }
        },
        getImageUrl(sku) {
            if (!sku) return 'https://placehold.co/400x400?text=Sem+Imagem';
            // Tenta carregar a imagem pelo SKU
            return `/imagens/${sku}.jpg`;
        },
        handleImageError(e) {
            // Se falhar, mostra placeholder
            if (!e.target.src.includes('placehold.co')) {
                e.target.src = 'https://placehold.co/400x400?text=Sem+Imagem';
            }
        },
        resetFilters() {
            this.search = '';
            this.selectedCategory = '';
            this.currentPage = 1;
        },
        async fetchData() {
            this.loading = true;
            try {
                const response = await fetch('/api/produtos');
                const data = await response.json();
                this.products = data.produtos || [];
                this.lastUpdate = data.ultima_atualizacao;
            } catch (error) {
                console.error('Erro ao carregar dados:', error);
                // Don't show error alert on initial load if empty, just show empty state
            } finally {
                this.loading = false;
            }
        },
        async fetchHistory(sku) {
            try {
                const response = await fetch(`/api/historico/${sku}`);
                const data = await response.json();
                this.priceHistory = data;
            } catch (error) {
                console.error('Erro ao carregar histórico:', error);
                this.priceHistory = [];
            }
        },
        async openDashboard() {
            this.showDashboardModal = true;
            try {
                const response = await fetch('/api/dashboard');
                const data = await response.json();
                this.dashboardStats = data;
            } catch (error) {
                console.error('Erro ao carregar dashboard:', error);
                Swal.fire('Erro', 'Não foi possível carregar os dados do dashboard.', 'error');
            }
        },
        async handleImageUpload(event, sku) {
            const file = event.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('image', file);

            try {
                Swal.fire({
                    title: 'Enviando imagem...',
                    text: 'Aguarde um momento',
                    allowOutsideClick: false,
                    didOpen: () => { Swal.showLoading(); }
                });

                const response = await fetch(`/api/upload-image/${sku}`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    Swal.fire({
                        title: 'Sucesso!',
                        text: 'Imagem atualizada. Pode ser necessário limpar o cache do navegador para ver a mudança.',
                        icon: 'success',
                        timer: 2000
                    });
                    // Force reload image by appending timestamp
                    const img = document.querySelector(`img[src*="${sku}.jpg"]`);
                    if (img) {
                        img.src = `/imagens/${sku}.jpg?t=${new Date().getTime()}`;
                    }
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                Swal.fire('Erro', error.message || 'Falha ao enviar imagem.', 'error');
            }
        },
        handleFileSelect(event) {
            this.selectedFile = event.target.files[0];
        },
        handleDrop(event) {
            const file = event.dataTransfer.files[0];
            if (file && file.name.endsWith('.csv')) {
                this.selectedFile = file;
            } else {
                Swal.fire('Arquivo Inválido', 'Por favor, envie apenas arquivos CSV.', 'warning');
            }
        },
        async uploadFile() {
            if (!this.selectedFile) return;
            
            this.uploading = true;
            const formData = new FormData();
            formData.append('file', this.selectedFile);
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    Swal.fire({
                        title: 'Sucesso!',
                        text: 'Estoque atualizado com sucesso.',
                        icon: 'success',
                        timer: 2000,
                        showConfirmButton: false
                    });
                    this.showUploadModal = false;
                    this.selectedFile = null;
                    this.fetchData();
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                Swal.fire('Erro', error.message || 'Falha ao enviar arquivo.', 'error');
            } finally {
                this.uploading = false;
            }
        },
        formatPrice(val) {
            if (!val) return '0,00';
            return parseFloat(val).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        },
        setTheme(themeKey) {
            this.currentTheme = themeKey;
            localStorage.setItem('theme', themeKey);
            this.applyTheme(themeKey);
        },
        applyTheme(themeKey) {
            const theme = this.themes[themeKey];
            if (!theme) return;

            const root = document.documentElement;
            const colors = theme.colors;

            // Apply colors to CSS variables or classes
            const styleId = 'dynamic-theme-styles';
            let styleTag = document.getElementById(styleId);
            if (!styleTag) {
                styleTag = document.createElement('style');
                styleTag.id = styleId;
                document.head.appendChild(styleTag);
            }

            const isDark = themeKey !== 'aqua';

            styleTag.innerHTML = `
                :root {
                    --color-primary: ${colors.primary};
                    --color-secondary: ${colors.secondary};
                    --color-bg: ${colors.bg};
                    --color-text: ${colors.text};
                    --color-card: ${colors.card};
                    --color-border: ${colors.border || '#e5e7eb'};
                    --color-header-bg: ${colors.headerBg || '#111827'};
                    --color-header-text: ${colors.headerText || '#ffffff'};
                }
                body { background-color: var(--color-bg) !important; color: var(--color-text) !important; }
                
                /* Colors */
                .bg-primary { background-color: var(--color-primary) !important; }
                .text-primary { color: var(--color-primary) !important; }
                .text-secondary { color: var(--color-secondary) !important; }
                .border-primary { border-color: var(--color-primary) !important; }
                
                /* Backgrounds */
                .bg-white { background-color: var(--color-card) !important; }
                .bg-gray-50 { background-color: var(--color-bg) !important; filter: brightness(0.95); }
                .dark\\:bg-slate-800 { background-color: var(--color-card) !important; }
                .dark\\:bg-slate-900 { background-color: var(--color-bg) !important; }

                /* Text - Scoped to avoid breaking header */
                body .text-gray-900, body .text-gray-800, body .text-gray-700 { color: var(--color-text) !important; }
                body .text-gray-600, body .text-gray-500 { color: var(--color-text) !important; opacity: 0.7; }
                
                /* Header Specifics */
                nav { background-color: var(--color-header-bg) !important; color: var(--color-header-text) !important; }
                nav .text-gray-400 { color: var(--color-header-text) !important; opacity: 0.7; }
                nav .text-gray-400:hover { color: var(--color-header-text) !important; opacity: 1; }
                nav input { 
                    background-color: rgba(255,255,255,0.1) !important; 
                    color: var(--color-header-text) !important; 
                    border-color: rgba(255,255,255,0.2) !important;
                }
                nav input::placeholder { color: var(--color-header-text) !important; opacity: 0.5; }

                /* Borders */
                .border-gray-200, .border-gray-100, .border-gray-300, .border-gray-50 { border-color: var(--color-border) !important; }
                
                /* Inputs (General) */
                main input, main select, main textarea, .modal input {
                    background-color: var(--color-card) !important;
                    color: var(--color-text) !important;
                    border-color: var(--color-border) !important;
                }

                /* Category Select Specific */
                .category-select-container {
                    background-color: var(--color-card) !important;
                    border-color: var(--color-border) !important;
                }
                .category-select-container select {
                    background-color: transparent !important;
                    color: var(--color-text) !important;
                }
                .category-select-container select option {
                    background-color: var(--color-card) !important;
                    color: var(--color-text) !important;
                }
                
                /* Dark Theme Adjustments */
                ${isDark ? `
                    .hover\\:bg-gray-50:hover { background-color: rgba(255,255,255,0.05) !important; }
                    .shadow-sm { box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.3) !important; }
                    
                    /* Fix specific dark mode issues */
                    .bg-gray-100 { background-color: rgba(255,255,255,0.05) !important; }
                    .text-gray-500 { color: rgba(255,255,255,0.6) !important; }
                ` : ''}

                /* High Contrast Specific */
                ${themeKey === 'contrast' ? `
                    .border, .border-t, .border-b { border-width: 2px !important; }
                    * { font-weight: 600 !important; }
                ` : ''}
            `;
        },
        toggleDarkMode() {
            // Legacy support or switch to specific dark theme
            this.setTheme(this.currentTheme === 'dark' ? 'aqua' : 'dark');
        },
        loadTheme() {
            const savedTheme = localStorage.getItem('theme') || 'aqua';
            this.setTheme(savedTheme);
        },
        toggleLowStock() {
            this.onlyLowStock = !this.onlyLowStock;
            this.currentPage = 1;
        },
        async startScanner() {
            this.showScanner = true;
            await this.$nextTick();
            
            if (!this.html5QrCode) {
                this.html5QrCode = new Html5Qrcode("reader");
            }

            try {
                const cameras = await Html5Qrcode.getCameras();
                this.cameras = cameras;
                
                if (cameras && cameras.length) {
                    // Tenta encontrar câmera traseira
                    let cameraId = cameras[0].id;
                    // Heurística simples para câmera traseira
                    const backCamera = cameras.find(c => c.label.toLowerCase().includes('back') || c.label.toLowerCase().includes('traseira') || c.label.toLowerCase().includes('environment'));
                    if (backCamera) {
                        cameraId = backCamera.id;
                        this.currentCameraIndex = cameras.indexOf(backCamera);
                    }

                    await this.html5QrCode.start(
                        cameraId, 
                        {
                            fps: 10,
                            qrbox: { width: 250, height: 250 },
                            aspectRatio: 1.0
                        },
                        this.onScanSuccess,
                        this.onScanFailure
                    );
                } else {
                    Swal.fire('Erro', 'Nenhuma câmera encontrada.', 'error');
                    this.showScanner = false;
                }
            } catch (err) {
                console.error(err);
                Swal.fire('Erro', 'Erro ao iniciar câmera: ' + err, 'error');
                this.showScanner = false;
            }
        },
        async stopScanner() {
            if (this.html5QrCode && this.html5QrCode.isScanning) {
                try {
                    await this.html5QrCode.stop();
                    this.html5QrCode.clear();
                } catch (e) {
                    console.error("Failed to stop scanner", e);
                }
            }
            this.showScanner = false;
        },
        async switchCamera() {
            if (this.cameras.length < 2) return;
            
            if (this.html5QrCode && this.html5QrCode.isScanning) {
                await this.html5QrCode.stop();
            }
            
            this.currentCameraIndex = (this.currentCameraIndex + 1) % this.cameras.length;
            const cameraId = this.cameras[this.currentCameraIndex].id;
            
            await this.html5QrCode.start(
                cameraId, 
                {
                    fps: 10,
                    qrbox: { width: 250, height: 250 },
                    aspectRatio: 1.0
                },
                this.onScanSuccess,
                this.onScanFailure
            );
        },
        onScanSuccess(decodedText, decodedResult) {
            // Handle on success condition with the decoded message.
            console.log(`Scan result ${decodedText}`, decodedResult);
            
            if (this.isConferenceMode) {
                this.handleConferenceScan(decodedText);
            } else {
                this.search = decodedText;
                this.stopScanner();
                Swal.fire({
                    title: 'Código Detectado!',
                    text: `Buscando por: ${decodedText}`,
                    icon: 'success',
                    timer: 1500,
                    showConfirmButton: false
                });
            }
        },
        onScanFailure(error) {
            // handle scan failure, usually better to ignore and keep scanning.
            // console.warn(`Code scan error = ${error}`);
        },
        openProductDetails(product) {
            this.selectedProduct = product;
            this.showProductModal = true;
            this.fetchHistory(product.SKU);
        },
        closeProductModal() {
            this.showProductModal = false;
            this.selectedProduct = null;
            this.priceHistory = [];
        },
        
        // Bulk Selection Methods
        toggleSelection(sku) {
            const index = this.selectedItems.indexOf(sku);
            if (index === -1) {
                this.selectedItems.push(sku);
            } else {
                this.selectedItems.splice(index, 1);
            }
        },
        toggleSelectAll() {
            if (this.allSelected) {
                // Deselect current page items
                const pageSkus = this.paginatedProducts.map(p => p.SKU);
                this.selectedItems = this.selectedItems.filter(sku => !pageSkus.includes(sku));
            } else {
                // Select current page items
                const pageSkus = this.paginatedProducts.map(p => p.SKU);
                pageSkus.forEach(sku => {
                    if (!this.selectedItems.includes(sku)) {
                        this.selectedItems.push(sku);
                    }
                });
            }
        },
        printSelectedLabels() {
            if (this.selectedItems.length === 0) return;
            
            const productsToPrint = this.products.filter(p => this.selectedItems.includes(p.SKU));
            
            const printWindow = window.open('', '', 'width=800,height=600');
            const date = new Date().toLocaleDateString('pt-BR');
            
            let labelsHtml = productsToPrint.map(product => `
                <div class="label">
                    <div class="header">
                        <span class="brand">${product['Meta: _marca'] || 'AQUAFLORA'}</span>
                        <span class="date">${date}</span>
                    </div>
                    <div class="product-name">${product.Name}</div>
                    <div class="price-box">
                        <span class="currency">R$</span>
                        <span class="price">${this.formatPrice(product['Regular price'])}</span>
                    </div>
                    <div class="footer">
                        <span class="sku">SKU: ${product.SKU}</span>
                    </div>
                </div>
            `).join('');

            printWindow.document.write(`
                <html>
                <head>
                    <title>Etiquetas - ${productsToPrint.length} itens</title>
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
                        body { 
                            font-family: 'Inter', sans-serif; 
                            margin: 0; 
                            padding: 20px;
                        }
                        .label-container {
                            display: grid;
                            grid-template-columns: repeat(auto-fill, 10cm);
                            gap: 10px;
                        }
                        .label {
                            width: 10cm;
                            height: 5cm;
                            border: 1px dashed #ccc;
                            padding: 15px;
                            box-sizing: border-box;
                            display: flex;
                            flex-direction: column;
                            justify-content: space-between;
                            page-break-inside: avoid;
                        }
                        .header { display: flex; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 5px; }
                        .brand { font-weight: 900; text-transform: uppercase; font-size: 14px; }
                        .date { font-size: 12px; }
                        .product-name { font-size: 16px; font-weight: 700; margin: 10px 0; line-height: 1.2; max-height: 2.4em; overflow: hidden; }
                        .price-box { font-size: 42px; font-weight: 900; text-align: center; margin: 5px 0; }
                        .currency { font-size: 20px; vertical-align: top; }
                        .footer { text-align: center; font-size: 12px; border-top: 1px solid #000; padding-top: 5px; }
                        @media print {
                            .label { border: none; }
                        }
                    </style>
                </head>
                <body>
                    <div class="label-container">
                        ${labelsHtml}
                    </div>
                    <script>
                        window.onload = function() { window.print(); }
                    <\/script>
                </body>
                </html>
            `);
            printWindow.document.close();
        },
        
        // Conference Mode
        startConference() {
            this.isConferenceMode = true;
            this.showConferenceModal = true;
            this.conferenceItems = [];
            this.startScanner();
        },
        stopConference() {
            this.isConferenceMode = false;
            this.showConferenceModal = false;
            this.stopScanner();
        },
        handleConferenceScan(code) {
            // Find product
            const product = this.products.find(p => p.SKU === code || p.Name.includes(code)); // Simple match
            
            if (product) {
                const existing = this.conferenceItems.find(i => i.sku === product.SKU);
                if (existing) {
                    existing.count++;
                } else {
                    this.conferenceItems.unshift({
                        sku: product.SKU,
                        name: product.Name,
                        systemStock: Number(product.Stock),
                        count: 1
                    });
                }
                
                const audio = new Audio('/static/beep.mp3'); // Optional beep
                // audio.play().catch(e => {}); 
                
                Swal.fire({
                    title: 'Bipado!',
                    text: `${product.Name}`,
                    icon: 'success',
                    timer: 800,
                    showConfirmButton: false,
                    position: 'top-end',
                    toast: true
                });
            } else {
                Swal.fire({
                    title: 'Não Encontrado',
                    text: `Produto com código ${code} não encontrado`,
                    icon: 'warning',
                    timer: 2000
                });
            }
        },

        printLabel(product) {
            const printWindow = window.open('', '', 'width=600,height=400');
            const date = new Date().toLocaleDateString('pt-BR');
            
            printWindow.document.write(`
                <html>
                <head>
                    <title>Etiqueta - ${product.Name}</title>
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
                        body { 
                            font-family: 'Inter', sans-serif; 
                            margin: 0; 
                            padding: 20px;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            min-height: 100vh;
                            background: #f0f0f0;
                        }
                        .label-container {
                            background: white;
                            width: 300px; /* Largura padrão de etiqueta */
                            padding: 15px;
                            border: 1px dashed #ccc;
                            text-align: center;
                            position: relative;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        }
                        .header {
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            gap: 10px;
                            margin-bottom: 10px;
                            border-bottom: 2px solid #000;
                            padding-bottom: 5px;
                        }
                        .logo { height: 30px; width: auto; }
                        .brand-name { font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }
                        .product-name { 
                            font-size: 14px; 
                            font-weight: 700; 
                            margin-bottom: 10px; 
                            line-height: 1.3;
                            min-height: 36px;
                            display: -webkit-box;
                            -webkit-line-clamp: 2;
                            -webkit-box-orient: vertical;
                            overflow: hidden;
                        }
                        .price-container {
                            background: #000;
                            color: #fff;
                            padding: 5px;
                            border-radius: 4px;
                            margin: 10px 0;
                        }
                        .price-label { font-size: 10px; text-transform: uppercase; opacity: 0.8; }
                        .price { font-size: 28px; font-weight: 900; }
                        .meta {
                            display: flex;
                            justify-content: space-between;
                            font-size: 10px;
                            color: #000;
                            margin-top: 10px;
                            border-top: 1px solid #eee;
                            padding-top: 5px;
                        }
                        .barcode {
                            margin-top: 8px;
                            font-family: 'Courier New', monospace;
                            font-weight: bold;
                            font-size: 12px;
                            letter-spacing: 3px;
                        }
                        @media print {
                            body { background: none; padding: 0; min-height: auto; display: block; }
                            .label-container { 
                                width: 100%; 
                                max-width: 100%; 
                                border: none; 
                                box-shadow: none; 
                                padding: 0;
                                page-break-inside: avoid;
                            }
                            .price-container {
                                background: #000 !important;
                                color: #fff !important;
                                -webkit-print-color-adjust: exact;
                                print-color-adjust: exact;
                            }
                        }
                    </style>
                </head>
                <body>
                    <div class="label-container">
                        <div class="header">
                            <img src="/static/logo.png" class="logo" alt="Logo">
                            <span class="brand-name">AquaFlora</span>
                        </div>
                        
                        <div class="product-name">${product.Name}</div>
                        
                        <div class="price-container">
                            <div class="price-label">Preço à Vista</div>
                            <div class="price">R$ ${this.formatPrice(product['Regular price'])}</div>
                        </div>
                        
                        <div class="barcode">*${product.SKU}*</div>
                        
                        <div class="meta">
                            <span>SKU: <strong>${product.SKU}</strong></span>
                            <span>${date}</span>
                        </div>
                    </div>
                    <script>
                        window.onload = function() { 
                            setTimeout(() => {
                                window.print(); 
                                window.close();
                            }, 500);
                        }
                    <\/script>
                </body>
                </html>
            `);
            printWindow.document.close();
        }
    }
}).mount('#app');
