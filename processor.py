import pandas as pd
import os
import json
import csv
import re
import glob
import datetime

class StockProcessor:
    def __init__(self, file_path, images_folder=None):
        self.file_path = file_path
        self.images_folder = images_folder
        self.target_columns = [
            'SKU', 'Name', 'Regular price', 'Categories', 'Meta: _marca', 'Stock',
            'Description', 'Short description', 'Weight (kg)', 'Meta: _custo'
        ]
        
        # Cache
        self._cache = None
        self._last_mtime = 0
        
        # Marcas Conhecidas (Ported from JS)
        self.marcas_conhecidas = {
            'royal canin': 'Royal Canin', 'royalcanin': 'Royal Canin', 'premier': 'Premier', 
            'premier pet': 'Premier Pet', 'golden': 'Golden', 'golden formula': 'Golden Formula',
            'farmina': 'Farmina', 'farmina n&d': 'Farmina N&D', 'origen': 'Origen', 'acana': 'Acana',
            'taste of the wild': 'Taste of the Wild', 'hills': "Hill's", 'purina': 'Purina',
            'proplan': 'Pro Plan', 'pro plan': 'Pro Plan', 'pedigree': 'Pedigree', 'whiskas': 'Whiskas',
            'friskies': 'Friskies', 'dog chow': 'Dog Chow', 'cat chow': 'Cat Chow', 'special dog': 'Special Dog',
            'special cat': 'Special Cat', 'luck dog': 'Luck Dog', 'luck cat': 'Luck Cat', 'max': 'Max',
            'max cat': 'Max Cat', 'max dog': 'Max Dog', 'total': 'Total', 'total dog': 'Total Dog',
            'total cat': 'Total Cat', 'sabor': 'Sabor & Vida', 'sabor e vida': 'Sabor & Vida',
            'sabor vida': 'Sabor & Vida', 'guabi': 'Guabi', 'guabi natural': 'Guabi Natural',
            'equilibrio': 'Equilíbrio', 'naturalis': 'Naturalis', 'nexgard': 'NexGard', 'bravecto': 'Bravecto',
            'simparic': 'Simparic', 'revolution': 'Revolution', 'advocate': 'Advocate', 'frontline': 'Frontline',
            'seresto': 'Seresto', 'heartgard': 'Heartgard', 'drontal': 'Drontal', 'vermifugo': 'Vermífugo',
            'antipulgas': 'Antipulgas', 'zoetis': 'Zoetis', 'virbac': 'Virbac', 'agener': 'Agener',
            'ceva': 'Ceva', 'merial': 'Merial', 'petbrilho': 'Pet Brilho', 'pet society': 'Pet Society',
            'plush': 'Plush', 'nasus': 'Nasus', 'kelldrin': 'Kelldrin', 'vitor': 'Vitor', 'vitalab': 'Vitalab',
            'biovet': 'Biovet', 'vetnil': 'Vetnil', 'ecopet': 'Ecopet', 'alcon': 'Alcon', 'tetra': 'Tetra',
            'sera': 'Sera', 'tropical': 'Tropical', 'nutrafin': 'Nutrafin', 'ocean tech': 'Ocean Tech',
            'oceantech': 'Ocean Tech', 'boyu': 'Boyu', 'sarlo': 'Sarlo', 'sarlo better': 'Sarlo Better',
            'atman': 'Atman', 'aquatech': 'Aquatech', 'resun': 'Resun', 'megazoo': 'Megazoo',
            'alimento': 'Alimento', 'nutrópica': 'Nutrópica', 'nutropica': 'Nutrópica', 'zootekna': 'Zootekna',
            'poytara': 'Poytara', 'trinca ferro': 'Trinca Ferro', 'genco': 'Genco', 'hidroazul': 'Hidroazul',
            'bel gard': 'Bel Gard', 'belguard': 'Bel Gard', 'barranets': 'Barranets', 'HTH': 'HTH',
            'acquazero': 'Acquazero', 'tramontina': 'Tramontina', 'vonder': 'Vonder', 'western': 'Western',
            'nautika': 'Nautika', 'coleman': 'Coleman', 'guepardo': 'Guepardo', 'mor': 'Mor',
            'invictus': 'Invictus', 'marine sports': 'Marine Sports', 'maruri': 'Maruri', 'daiwa': 'Daiwa',
            'shimano': 'Shimano', 'albatroz': 'Albatroz', 'saint': 'Saint', 'sumax': 'Sumax', 'forth': 'Forth',
            'dimy': 'Dimy', 'nutriplan': 'Nutriplan', 'biofertil': 'Biofertil', 'bionatural': 'BioNatural',
            'vitaplan': 'Vitaplan', 'plantafol': 'Plantafol', 'palheiro': 'Palheiro', 'smoking': 'Smoking',
            'zig zag': 'Zig Zag', 'zigzag': 'Zig Zag', 'raw': 'RAW', 'club modiano': 'Club Modiano', 'copag': 'Copag'
        }

        # Regex Replacements (Ported from Python)
        self.replacements = {
             r'\bCes\b': 'Cães', r'\bRacao\b': 'Ração', r'\bRao\b': 'Ração', r'\bMaA\b': 'Maçã',
             r'\bDGua\b': "D'Água", r'\bAcrilico\b': 'Acrílico', r'\bPlastico\b': 'Plástico',
             r'\bEletrico\b': 'Elétrico', r'\bRape\b': 'Rapé', r'\bPassaros\b': 'Pássaros',
             r'\bHerbivoros\b': 'Herbívoros', r'\bCeramico\b': 'Cerâmico', r'\bAutomatico\b': 'Automático',
             r'\bCb\.(?=\s|$)': 'Cabo', r'\bBainha Pl\b': 'Bainha Plástica', r'\b110v\b': '110V',
             r'\b220v\b': '220V', r'\b300g\b': '300g', r'\bKg\b': 'kg', r'\bkg\b': 'kg',
             r'\bUnid\b': 'Unid.', r'\bUn\.(?=\s|$)': 'Un.', r'\bMts\b': 'Metros', r'\bMt\b': 'Metro',
             r'\bmt\b': 'Metros', r'\bCm\b': 'cm', r'\bMm\b': 'mm', r'\bLts\b': 'Litros',
             r'\bLt\b': 'Litro', r'\bMl\b': 'ml', r'\bW\b': 'W', r'\bV\b': 'V', r'\bA\b': 'A',
             r'\bCv\b': 'CV', r'\bHp\b': 'HP', r'\bPh\b': 'pH', r'\bPpm\b': 'ppm', r'\bKh\b': 'KH',
             r'\bGh\b': 'GH', r'\bUv\b': 'UV', r'\bLed\b': 'LED', r'\bRgb\b': 'RGB', r'\bUsb\b': 'USB',
             r'\bBivolt\b': 'Bivolt', r'\bInox\b': 'Inox', r'\bPvc\b': 'PVC', r'\bAbs\b': 'ABS',
             r'\bPp\b': 'PP', r'\bPe\b': 'PE', r'\bPet\b': 'PET', r'\bEva\b': 'EVA', r'\bTnt\b': 'TNT',
             r'\bMdf\b': 'MDF', r'\bMdp\b': 'MDP', r'\bOsso\b': 'Osso', r'\bCouro\b': 'Couro',
             r'\bNylon\b': 'Nylon', r'\bPoliester\b': 'Poliéster', r'\bAlgodao\b': 'Algodão',
             r'\bAluminio\b': 'Alumínio', r'\bSeda\b': 'Seda', r'\bVeludo\b': 'Veludo',
             r'\bCamurca\b': 'Camurça', r'\bJeans\b': 'Jeans', r'\bLona\b': 'Lona', r'\bJuta\b': 'Juta',
             r'\bSisal\b': 'Sisal', r'\bPalha\b': 'Palha', r'\bBambu\b': 'Bambu', r'\bMadeira\b': 'Madeira',
             r'\bVidro\b': 'Vidro', r'\bCristal\b': 'Cristal', r'\bPorcelana\b': 'Porcelana',
             r'\bCeramica\b': 'Cerâmica', r'\bBarro\b': 'Barro', r'\bGesso\b': 'Gesso',
             r'\bCimento\b': 'Cimento', r'\bPedra\b': 'Pedra', r'\bMarmore\b': 'Mármore',
             r'\bGranito\b': 'Granito', r'\bAreia\b': 'Areia', r'\bTerra\b': 'Terra',
             r'\bSubstrato\b': 'Substrato', r'\bAdubo\b': 'Adubo', r'\bFertilizante\b': 'Fertilizante',
             r'\bSemente\b': 'Semente', r'\bMuda\b': 'Muda', r'\bPlanta\b': 'Planta', r'\bFlor\b': 'Flor',
             r'\bFruta\b': 'Fruta', r'\bLegume\b': 'Legume', r'\bVerdura\b': 'Verdura',
             r'\bTempero\b': 'Tempero', r'\bErva\b': 'Erva', r'\bCha\b': 'Chá', r'\bCafe\b': 'Café',
             r'\bAcucar\b': 'Açúcar', r'\bSal\b': 'Sal', r'\bPimenta\b': 'Pimenta', r'\bOleo\b': 'Óleo',
             r'\bAzeite\b': 'Azeite', r'\bVinagre\b': 'Vinagre', r'\bMolho\b': 'Molho',
             r'\bConserva\b': 'Conserva', r'\bDoce\b': 'Doce', r'\bBiscoito\b': 'Biscoito',
             r'\bBolacha\b': 'Bolacha', r'\bBolo\b': 'Bolo', r'\bPao\b': 'Pão', r'\bTorrada\b': 'Torrada',
             r'\bSnack\b': 'Snack', r'\bPetisco\b': 'Petisco', r'\bOssinho\b': 'Ossinho',
             r'\bBifinho\b': 'Bifinho', r'\bPalito\b': 'Palito', r'\bSache\b': 'Sachê', r'\bLata\b': 'Lata',
             r'\bPote\b': 'Pote', r'\bCaixa\b': 'Caixa', r'\bSaco\b': 'Saco', r'\bFardo\b': 'Fardo',
             r'\bKit\b': 'Kit', r'\bJogo\b': 'Jogo', r'\bConjunto\b': 'Conjunto', r'\bPar\b': 'Par',
             r'\bUnidade\b': 'Unidade', r'\bPeca\b': 'Peça', r'\bMetro\b': 'Metro', r'\bRolo\b': 'Rolo',
             r'\bBobina\b': 'Bobina', r'\bCartela\b': 'Cartela', r'\bDisplay\b': 'Display',
             r'\bBlister\b': 'Blister', r'\bGranel\b': 'Granel', r'\bRefil\b': 'Refil',
             r'\bReparo\b': 'Reparo', r'\bAcessorio\b': 'Acessório',
             r'\bPeca De Reposicao\b': 'Peça de Reposição', r'\bManutencao\b': 'Manutenção',
             r'\bLimpeza\b': 'Limpeza', r'\bHigiene\b': 'Higiene', r'\bBeleza\b': 'Beleza',
             r'\bSaude\b': 'Saúde', r'\bMedicamento\b': 'Medicamento', r'\bRemedio\b': 'Remédio',
             r'\bVacina\b': 'Vacina', r'\bVermifugo\b': 'Vermífugo', r'\bAntipulgas\b': 'Antipulgas',
             r'\bCarrapaticida\b': 'Carrapaticida', r'\bShampoo\b': 'Shampoo',
             r'\bCondicionador\b': 'Condicionador', r'\bSabonete\b': 'Sabonete', r'\bPerfume\b': 'Perfume',
             r'\bColonia\b': 'Colônia', r'\bTalco\b': 'Talco', r'\bAreia Sanitaria\b': 'Areia Sanitária',
             r'\bTapete Higienico\b': 'Tapete Higiênico', r'\bFralda\b': 'Fralda', r'\bBanheiro\b': 'Banheiro',
             r'\bCaixa De Areia\b': 'Caixa de Areia', r'\bPah\b': 'Pá', r'\bComedouro\b': 'Comedouro',
             r'\bBebedouro\b': 'Bebedouro', r'\bFonte\b': 'Fonte', r'\bAlimentador\b': 'Alimentador',
             r'\bColeira\b': 'Coleira', r'\bGuia\b': 'Guia', r'\bPeitoral\b': 'Peitoral',
             r'\bEnforcador\b': 'Enforcador', r'\bFocinheira\b': 'Focinheira',
             r'\bIdentificador\b': 'Identificador', r'\bPingente\b': 'Pingente', r'\bRoupa\b': 'Roupa',
             r'\bCama\b': 'Cama', r'\bColchonete\b': 'Colchonete', r'\bAlmofada\b': 'Almofada',
             r'\bCobertor\b': 'Cobertor', r'\bManta\b': 'Manta', r'\bToca\b': 'Toca',
             r'\bCasinha\b': 'Casinha', r'\bGaiola\b': 'Gaiola', r'\bViveiro\b': 'Viveiro',
             r'\bAquario\b': 'Aquário', r'\bTerrario\b': 'Terrário', r'\bTransporte\b': 'Transporte',
             r'\bCaixa De Transporte\b': 'Caixa de Transporte', r'\bBolsa\b': 'Bolsa',
             r'\bMochila\b': 'Mochila', r'\bCarrinho\b': 'Carrinho', r'\bBrinquedo\b': 'Brinquedo',
             r'\bArranhador\b': 'Arranhador', r'\bTunel\b': 'Túnel', r'\bBolinha\b': 'Bolinha',
             r'\bCorda\b': 'Corda', r'\bPelucia\b': 'Pelúcia', r'\bLatex\b': 'Látex',
             r'\bBorracha\b': 'Borracha', r'\bVinil\b': 'Vinil', r'\bTecido\b': 'Tecido',
             r'\bInterativo\b': 'Interativo', r'\bInteligente\b': 'Inteligente',
             r'\bEducativo\b': 'Educativo', r'\bAdestramento\b': 'Adestramento',
             r'\bComportamento\b': 'Comportamento', r'\bAnti-Latido\b': 'Anti-Latido',
             r'\bAnti-Mordida\b': 'Anti-Mordida', r'\bRepelente\b': 'Repelente', r'\bAtrativo\b': 'Atrativo',
             r'\bCatnip\b': 'Catnip', r'\bErva De Gato\b': 'Erva de Gato', r'\bGraminha\b': 'Graminha',
             r'\bPassaro\b': 'Pássaro', r'\bAve\b': 'Ave', r'\bAves\b': 'Aves', r'\bPeixe\b': 'Peixe',
             r'\bPeixes\b': 'Peixes', r'\bReptil\b': 'Réptil', r'\bRepteis\b': 'Répteis',
             r'\bRoedor\b': 'Roedor', r'\bRoedores\b': 'Roedores', r'\bCoelho\b': 'Coelho',
             r'\bCoelhos\b': 'Coelhos', r'\bHamster\b': 'Hamster', r'\bHamsters\b': 'Hamsters',
             r'\bChinchila\b': 'Chinchila', r'\bChinchilas\b': 'Chinchilas',
             r'\bPorquinho Da India\b': 'Porquinho da Índia', r'\bFurao\b': 'Furão', r'\bFuroes\b': 'Furões',
             r'\bCavalo\b': 'Cavalo', r'\bCavalos\b': 'Cavalos', r'\bEquino\b': 'Equino',
             r'\bEquinos\b': 'Equinos', r'\bBovino\b': 'Bovino', r'\bBovinos\b': 'Bovinos',
             r'\bSuino\b': 'Suíno', r'\bSuinos\b': 'Suínos', r'\bCaprino\b': 'Caprino',
             r'\bCaprinos\b': 'Caprinos', r'\bOvino\b': 'Ovino', r'\bOvinos\b': 'Ovinos',
             r'\bAve De Corte\b': 'Ave de Corte', r'\bAve De Postura\b': 'Ave de Postura',
             r'\bAbelha\b': 'Abelha', r'\bAbelhas\b': 'Abelhas', r'\bJardim\b': 'Jardim',
             r'\bJardinagem\b': 'Jardinagem', r'\bPiscina\b': 'Piscina', r'\bCamping\b': 'Camping',
             r'\bPesca\b': 'Pesca', r'\bLazer\b': 'Lazer', r'\bChurrasco\b': 'Churrasco',
             r'\bDecoracao\b': 'Decoração', r'\bUtilidade Domestica\b': 'Utilidade Doméstica',
             r'\bFerramenta\b': 'Ferramenta', r'\bFerragem\b': 'Ferragem',
             r'\bMaterial De Construcao\b': 'Material de Construção', r'\bEletrica\b': 'Elétrica',
             r'\bHidraulica\b': 'Hidráulica', r'\bPintura\b': 'Pintura', r'\bAutomotivo\b': 'Automotivo',
             r'\bAgro\b': 'Agro', r'\bVeterinaria\b': 'Veterinária', r'\bPet Shop\b': 'Pet Shop',
             r'\bAgropecuaria\b': 'Agropecuária', r'\bFarmacia\b': 'Farmácia', r'\bClinica\b': 'Clínica',
             r'\bHospital\b': 'Hospital', r'\bLaboratorio\b': 'Laboratório', r'\bIndustria\b': 'Indústria',
             r'\bComercio\b': 'Comércio', r'\bServico\b': 'Serviço', r'\bEscritorio\b': 'Escritório',
             r'\bEscola\b': 'Escola', r'\bPapelaria\b': 'Papelaria', r'\bInformatica\b': 'Informática',
             r'\bEletronico\b': 'Eletrônico', r'\bCelular\b': 'Celular', r'\bTelefone\b': 'Telefone',
             r'\bAudio\b': 'Áudio', r'\bVideo\b': 'Vídeo', r'\bFoto\b': 'Foto', r'\bGame\b': 'Game',
             r'\bEsporte\b': 'Esporte', r'\bFitness\b': 'Fitness', r'\bSuplemento\b': 'Suplemento',
             r'\bVitamina\b': 'Vitamina', r'\bMineral\b': 'Mineral', r'\bProteina\b': 'Proteína',
             r'\bAminoacido\b': 'Aminoácido', r'\bEmagrecedor\b': 'Emagrecedor',
             r'\bTermogenico\b': 'Termogênico', r'\bPre-Treino\b': 'Pré-Treino',
             r'\bPos-Treino\b': 'Pós-Treino', r'\bBarra De Proteina\b': 'Barra de Proteína',
             r'\bBebida Esportiva\b': 'Bebida Esportiva', r'\bAcessorio Esportivo\b': 'Acessório Esportivo',
             r'\bRoupa Esportiva\b': 'Roupa Esportiva', r'\bCalcado Esportivo\b': 'Calçado Esportivo',
             r'\bEquipamento Esportivo\b': 'Equipamento Esportivo', r'\bBicicleta\b': 'Bicicleta',
             r'\bSkate\b': 'Skate', r'\bPatins\b': 'Patins', r'\bPatinete\b': 'Patinete',
             r'\bMoto\b': 'Moto', r'\bCarro\b': 'Carro', r'\bCaminhao\b': 'Caminhão',
             r'\bOnibus\b': 'Ônibus', r'\bTrator\b': 'Trator', r'\bMaquina Agricola\b': 'Máquina Agrícola',
             r'\bImplemento Agricola\b': 'Implemento Agrícola', r'\bPneu\b': 'Pneu', r'\bRoda\b': 'Roda',
             r'\bBateria\b': 'Bateria', r'\bOleo Lubrificante\b': 'Óleo Lubrificante',
             r'\bFiltro De Oleo\b': 'Filtro de Óleo', r'\bFiltro De Ar\b': 'Filtro de Ar',
             r'\bFiltro De Combustivel\b': 'Filtro de Combustível',
             r'\bPastilha De Freio\b': 'Pastilha de Freio', r'\bDisco De Freio\b': 'Disco de Freio',
             r'\bAmortecedor\b': 'Amortecedor', r'\bMola\b': 'Mola', r'\bSuspensao\b': 'Suspensão',
             r'\bDirecao\b': 'Direção', r'\bEmbreagem\b': 'Embreagem', r'\bCambio\b': 'Câmbio',
             r'\bMotor\b': 'Motor', r'\bEscapamento\b': 'Escapamento', r'\bCatalisador\b': 'Catalisador',
             r'\bRadiador\b': 'Radiador', r'\bAr Condicionado\b': 'Ar Condicionado',
             r'\bVidro Eletrico\b': 'Vidro Elétrico', r'\bTrava Eletrica\b': 'Trava Elétrica',
             r'\bAlarme\b': 'Alarme', r'\bSom Automotivo\b': 'Som Automotivo', r'\bGps\b': 'GPS',
             r'\bCamera De Re\b': 'Câmera de Ré', r'\bSensor De Estacionamento\b': 'Sensor de Estacionamento',
             r'\bFarol\b': 'Farol', r'\bLanterna\b': 'Lanterna', r'\bLampada\b': 'Lâmpada',
             r'\bEspelho\b': 'Espelho', r'\bRetrovisor\b': 'Retrovisor', r'\bParachoque\b': 'Para-choque',
             r'\bGrade\b': 'Grade', r'\bCapo\b': 'Capô', r'\bPorta\b': 'Porta',
             r'\bPorta-Malas\b': 'Porta-Malas', r'\bTeto Solar\b': 'Teto Solar', r'\bBanco\b': 'Banco',
             r'\bCapa De Banco\b': 'Capa de Banco', r'\bTapete Automotivo\b': 'Tapete Automotivo',
             r'\bVolante\b': 'Volante', r'\bManopla\b': 'Manopla', r'\bPedaleira\b': 'Pedaleira',
             r'\bCinto De Seguranca\b': 'Cinto de Segurança', r'\bCadeira De Bebe\b': 'Cadeira de Bebê',
             r'\bAssento De Elevacao\b': 'Assento de Elevação', r'\bBebe Conforto\b': 'Bebê Conforto',
             r'\bCarrinho De Bebe\b': 'Carrinho de Bebê', r'\bAndador\b': 'Andador', r'\bBerco\b': 'Berço',
             r'\bComoda\b': 'Cômoda', r'\bGuarda-Roupa\b': 'Guarda-Roupa', r'\bArmario\b': 'Armário',
             r'\bEstante\b': 'Estante', r'\bPrateleira\b': 'Prateleira', r'\bNicho\b': 'Nicho',
             r'\bMesa\b': 'Mesa', r'\bCadeira\b': 'Cadeira', r'\bBanqueta\b': 'Banqueta',
             r'\bSofa\b': 'Sofá', r'\bPoltrona\b': 'Poltrona', r'\bPuff\b': 'Puff', r'\bRack\b': 'Rack',
             r'\bPainel\b': 'Painel', r'\bHome Theater\b': 'Home Theater', r'\bTv\b': 'TV',
             r'\bSmart Tv\b': 'Smart TV', r'\bMonitor\b': 'Monitor', r'\bProjetor\b': 'Projetor',
             r'\bTela De Projecao\b': 'Tela de Projeção', r'\bSuporte Para Tv\b': 'Suporte para TV',
             r'\bAntena\b': 'Antena', r'\bReceptor\b': 'Receptor', r'\bConversor\b': 'Conversor',
             r'\bDvd Player\b': 'DVD Player', r'\bBlu-Ray Player\b': 'Blu-Ray Player',
             r'\bSoundbar\b': 'Soundbar', r'\bCaixa De Som\b': 'Caixa de Som',
             r'\bFone De Ouvido\b': 'Fone de Ouvido', r'\bMicrofone\b': 'Microfone',
             r'\bInstrumento Musical\b': 'Instrumento Musical', r'\bViolao\b': 'Violão',
             r'\bGuitarra\b': 'Guitarra', r'\bBaixo\b': 'Baixo', r'\bTeclado\b': 'Teclado',
             r'\bPiano\b': 'Piano', r'\bSopro\b': 'Sopro', r'\bPercussao\b': 'Percussão',
             r'\bAcessorio Musical\b': 'Acessório Musical', r'\bLivro\b': 'Livro', r'\bRevista\b': 'Revista',
             r'\bHq\b': 'HQ', r'\bManga\b': 'Mangá', r'\bCd\b': 'CD', r'\bDvd\b': 'DVD',
             r'\bBlu-Ray\b': 'Blu-Ray', r'\bVinil\b': 'Vinil', r'\bLp\b': 'LP', r'\bFilme\b': 'Filme',
             r'\bSerie\b': 'Série', r'\bDocumentario\b': 'Documentário', r'\bShow\b': 'Show',
             r'\bMusica\b': 'Música', r'\bJogo De Videogame\b': 'Jogo de Videogame', r'\bConsole\b': 'Console',
             r'\bControle\b': 'Controle', r'\bAcessorio Gamer\b': 'Acessório Gamer',
             r'\bPc Gamer\b': 'PC Gamer', r'\bNotebook Gamer\b': 'Notebook Gamer',
             r'\bMouse Gamer\b': 'Mouse Gamer', r'\bTeclado Gamer\b': 'Teclado Gamer',
             r'\bHeadset Gamer\b': 'Headset Gamer', r'\bCadeira Gamer\b': 'Cadeira Gamer',
             r'\bMesa Gamer\b': 'Mesa Gamer', r'\bMousepad Gamer\b': 'Mousepad Gamer',
             r'\bStreamer\b': 'Streamer', r'\bYoutuber\b': 'YouTuber', r'\bInfluencer\b': 'Influencer',
             r'\bCriador De Conteudo\b': 'Criador de Conteúdo', r'\bCamera Fotografica\b': 'Câmera Fotográfica',
             r'\bFilmadora\b': 'Filmadora', r'\bDrone\b': 'Drone', r'\bTripe\b': 'Tripé',
             r'\bIluminacao\b': 'Iluminação', r'\bEstudio\b': 'Estúdio', r'\bLente\b': 'Lente',
             r'\bFlash\b': 'Flash', r'\bCartao De Memoria\b': 'Cartão de Memória',
             r'\bHd Externo\b': 'HD Externo', r'\bSsd\b': 'SSD', r'\bPen Drive\b': 'Pen Drive',
             r'\bRoteador\b': 'Roteador', r'\bRepetidor\b': 'Repetidor', r'\bSwitch\b': 'Switch',
             r'\bModem\b': 'Modem', r'\bCabo De Rede\b': 'Cabo de Rede', r'\bServidor\b': 'Servidor',
             r'\bNobreak\b': 'Nobreak', r'\bEstabilizador\b': 'Estabilizador',
             r'\bFiltro De Linha\b': 'Filtro de Linha', r'\bExtensao\b': 'Extensão',
             r'\bAdaptador\b': 'Adaptador', r'\bHub\b': 'Hub', r'\bDock Station\b': 'Dock Station',
             r'\bCooler\b': 'Cooler', r'\bFonte De Alimentacao\b': 'Fonte de Alimentação',
             r'\bGabinete\b': 'Gabinete', r'\bPlaca Mae\b': 'Placa Mãe', r'\bProcessador\b': 'Processador',
             r'\bMemoria Ram\b': 'Memória RAM', r'\bPlaca De Video\b': 'Placa de Vídeo',
             r'\bPlaca De Som\b': 'Placa de Som', r'\bPlaca De Rede\b': 'Placa de Rede',
             r'\bDrive Optico\b': 'Drive Óptico', r'\bLeitor De Cartao\b': 'Leitor de Cartão',
             r'\bWebcam\b': 'Webcam', r'\bImpressora\b': 'Impressora', r'\bMultifuncional\b': 'Multifuncional',
             r'\bScanner\b': 'Scanner', r'\bCartucho\b': 'Cartucho', r'\bToner\b': 'Toner',
             r'\bPapel\b': 'Papel', r'\bEtiqueta\b': 'Etiqueta', r'\bEnvelope\b': 'Envelope',
             r'\bCaneta\b': 'Caneta', r'\bLapis\b': 'Lápis', r'\bBorracha\b': 'Borracha',
             r'\bApontador\b': 'Apontador', r'\bRegua\b': 'Régua', r'\bTesoura\b': 'Tesoura',
             r'\bCola\b': 'Cola', r'\bFita Adesiva\b': 'Fita Adesiva', r'\bGrampeador\b': 'Grampeador',
             r'\bPerfurador\b': 'Perfurador', r'\bPasta\b': 'Pasta', r'\bArquivo\b': 'Arquivo',
             r'\bOrganizador\b': 'Organizador', r'\bAgenda\b': 'Agenda', r'\bCaderno\b': 'Caderno',
             r'\bBloco De Notas\b': 'Bloco de Notas', r'\bPost-It\b': 'Post-it',
             r'\bQuadro Branco\b': 'Quadro Branco', r'\bMarcador\b': 'Marcador', r'\bApagador\b': 'Apagador',
             r'\bEstojo\b': 'Estojo', r'\bLancheira\b': 'Lancheira', r'\bGarrafa\b': 'Garrafa',
             r'\bCopo\b': 'Copo', r'\bCaneca\b': 'Caneca', r'\bTermica\b': 'Térmica',
             r'\bMarmita\b': 'Marmita', r'\bTalher\b': 'Talher', r'\bPrato\b': 'Prato',
             r'\bTigela\b': 'Tigela', r'\bJarra\b': 'Jarra', r'\bBule\b': 'Bule',
             r'\bChaleira\b': 'Chaleira', r'\bCafeteira\b': 'Cafeteira', r'\bLiquidificador\b': 'Liquidificador',
             r'\bBatedeira\b': 'Batedeira', r'\bProcessador De Alimentos\b': 'Processador de Alimentos',
             r'\bMixer\b': 'Mixer', r'\bEspremedor\b': 'Espremedor', r'\bSanduicheira\b': 'Sanduicheira',
             r'\bTorradeira\b': 'Torradeira', r'\bGrill\b': 'Grill', r'\bFritadeira\b': 'Fritadeira',
             r'\bAir Fryer\b': 'Air Fryer', r'\bPanela Eletrica\b': 'Panela Elétrica',
             r'\bForno Eletrico\b': 'Forno Elétrico', r'\bMicroondas\b': 'Micro-ondas',
             r'\bFogao\b': 'Fogão', r'\bCooktop\b': 'Cooktop', r'\bCoifa\b': 'Coifa',
             r'\bDepurador\b': 'Depurador', r'\bGeladeira\b': 'Geladeira', r'\bRefrigerador\b': 'Refrigerador',
             r'\bFreezer\b': 'Freezer', r'\bFrigobar\b': 'Frigobar', r'\bAdega\b': 'Adega',
             r'\bCervejeira\b': 'Cervejeira', r'\bLava-Loucas\b': 'Lava-Louças',
             r'\bLava-Roupas\b': 'Lava-Roupas', r'\bSecadora\b': 'Secadora', r'\bLava E Seca\b': 'Lava e Seca',
             r'\bCentrifuga\b': 'Centrífuga', r'\bFerro De Passar\b': 'Ferro de Passar',
             r'\bVaporizador\b': 'Vaporizador', r'\bAspirador De Po\b': 'Aspirador de Pó',
             r'\bRobo Aspirador\b': 'Robô Aspirador', r'\bEnceradeira\b': 'Enceradeira',
             r'\bLavadora De Alta Pressao\b': 'Lavadora de Alta Pressão', r'\bVentilador\b': 'Ventilador',
             r'\bCirculador De Ar\b': 'Circulador de Ar', r'\bClimatizador\b': 'Climatizador',
             r'\bAquecedor\b': 'Aquecedor', r'\bDesumidificador\b': 'Desumidificador',
             r'\bUmidificador\b': 'Umidificador', r'\bPurificador De Ar\b': 'Purificador de Ar',
             r'\bPurificador De Agua\b': 'Purificador de Água', r'\bFiltro De Agua\b': 'Filtro de Água',
             r'\bTorneira\b': 'Torneira', r'\bMisturador\b': 'Misturador', r'\bChuveiro\b': 'Chuveiro',
             r'\bDucha\b': 'Ducha', r'\bAssento Sanitario\b': 'Assento Sanitário',
             r'\bVaso Sanitario\b': 'Vaso Sanitário', r'\bCuba\b': 'Cuba', r'\bPia\b': 'Pia',
             r'\bTanque\b': 'Tanque', r'\bBox\b': 'Box', r'\bToalheiro\b': 'Toalheiro',
             r'\bSaboneteira\b': 'Saboneteira', r'\bPapeleira\b': 'Papeleira', r'\bCabide\b': 'Cabide',
             r'\bGancho\b': 'Gancho', r'\bLixeira\b': 'Lixeira', r'\bCesto\b': 'Cesto',
             r'\bBalde\b': 'Balde', r'\bBacia\b': 'Bacia', r'\bVassoura\b': 'Vassoura',
             r'\bRodo\b': 'Rodo', r'\bEscova\b': 'Escova', r'\bEsponja\b': 'Esponja',
             r'\bPano\b': 'Pano', r'\bFlanela\b': 'Flanela', r'\bAvental\b': 'Avental',
             r'\bTouca\b': 'Touca', r'\bMascara\b': 'Máscara', r'\bOculos\b': 'Óculos',
             r'\bProtetor Auricular\b': 'Protetor Auricular', r'\bCapacete\b': 'Capacete',
             r'\bBota\b': 'Bota', r'\bSapato\b': 'Sapato', r'\bTenis\b': 'Tênis',
             r'\bChinelo\b': 'Chinelo', r'\bSandalia\b': 'Sandália', r'\bSapatilha\b': 'Sapatilha',
             r'\bMeia\b': 'Meia', r'\bCalca\b': 'Calça', r'\bBermuda\b': 'Bermuda',
             r'\bShort\b': 'Short', r'\bSaia\b': 'Saia', r'\bVestido\b': 'Vestido',
             r'\bCamisa\b': 'Camisa', r'\bCamiseta\b': 'Camiseta', r'\bBlusa\b': 'Blusa',
             r'\bCasaco\b': 'Casaco', r'\bJaqueta\b': 'Jaqueta', r'\bMoletom\b': 'Moletom',
             r'\bSueter\b': 'Suéter', r'\bColete\b': 'Colete', r'\bTerno\b': 'Terno',
             r'\bGravata\b': 'Gravata', r'\bCinto\b': 'Cinto', r'\bBone\b': 'Boné',
             r'\bChapeu\b': 'Chapéu', r'\bGorro\b': 'Gorro', r'\bCachecol\b': 'Cachecol',
             r'\bRelogio\b': 'Relógio', r'\bOculos De Sol\b': 'Óculos de Sol', r'\bJoia\b': 'Joia',
             r'\bBijuteria\b': 'Bijuteria', r'\bAnel\b': 'Anel', r'\bBrinco\b': 'Brinco',
             r'\bColar\b': 'Colar', r'\bPulseira\b': 'Pulseira', r'\bTornozeleira\b': 'Tornozeleira',
             r'\bPiercing\b': 'Piercing', r'\bAlianca\b': 'Aliança', r'\bOuro\b': 'Ouro',
             r'\bPrata\b': 'Prata', r'\bBronze\b': 'Bronze', r'\bAco\b': 'Aço',
             r'\bTitanio\b': 'Titânio', r'\bPedra Preciosa\b': 'Pedra Preciosa',
             r'\bDiamante\b': 'Diamante', r'\bRubi\b': 'Rubi', r'\bEsmeralda\b': 'Esmeralda',
             r'\bSafira\b': 'Safira', r'\bPerola\b': 'Pérola', r'\bZirconia\b': 'Zircônia',
             r'\bReligioso\b': 'Religioso', r'\bEsoterico\b': 'Esotérico', r'\bMistico\b': 'Místico',
             r'\bArtesanato\b': 'Artesanato', r'\bFeito A Mao\b': 'Feito à Mão',
             r'\bPersonalizado\b': 'Personalizado', r'\bPresente\b': 'Presente',
             r'\bLembrancinha\b': 'Lembrancinha', r'\bFesta\b': 'Festa',
             r'\bAniversario\b': 'Aniversário', r'\bCasamento\b': 'Casamento',
             r'\bBatizado\b': 'Batizado', r'\bCha De Bebe\b': 'Chá de Bebê',
             r'\bCha De Cozinha\b': 'Chá de Cozinha', r'\bCha Bar\b': 'Chá Bar',
             r'\bDespedida De Solteiro\b': 'Despedida de Solteiro', r'\bFormatura\b': 'Formatura',
             r'\bNatal\b': 'Natal', r'\bAno Novo\b': 'Ano Novo', r'\bPascoa\b': 'Páscoa',
             r'\bDia Das Maes\b': 'Dia das Mães', r'\bDia Dos Pais\b': 'Dia dos Pais',
             r'\bDia Dos Namorados\b': 'Dia dos Namorados', r'\bDia Das Criancas\b': 'Dia das Crianças',
             r'\bBlack Friday\b': 'Black Friday', r'\bPromocao\b': 'Promoção', r'\bOferta\b': 'Oferta',
             r'\bDesconto\b': 'Desconto', r'\bLiquidação\b': 'Liquidação', r'\bSaldão\b': 'Saldão',
             r'\bOutlet\b': 'Outlet', r'\bLancamento\b': 'Lançamento', r'\bNovidade\b': 'Novidade',
             r'\bExclusivo\b': 'Exclusivo', r'\bLimitado\b': 'Limitado', r'\bEspecial\b': 'Especial',
             r'\bPremium\b': 'Premium', r'\bLuxo\b': 'Luxo', r'\bBasico\b': 'Básico',
             r'\bEssencial\b': 'Essencial', r'\bPadrao\b': 'Padrão', r'\bSimples\b': 'Simples',
             r'\bComposto\b': 'Composto', r'\bMisto\b': 'Misto', r'\bSortido\b': 'Sortido',
             r'\bVariado\b': 'Variado', r'\bDiverso\b': 'Diverso', r'\bOutro\b': 'Outro',
             r'\bAd\b': 'Adulto', r'\bPq\b': 'Pequeno', r'\bMd\b': 'Médio', r'\bGd\b': 'Grande',
             r'\bFil\b': 'Filhote', r'\bCast\b': 'Castrado', r'\bLig\b': 'Light', r'\bSen\b': 'Sênior',
             r'\bSenior\b': 'Sênior', r'\bRmg\b': 'Raças Médias e Grandes', r'\bRp\b': 'Raças Pequenas',
             r'\bNat\.\b': 'Natural', r'\bNat\b': 'Natural', r'\bSel\.\b': 'Seleção',
             r'\bSelecao\b': 'Seleção', r'\bPrem\b': 'Premium', r'\bEsp\b': 'Especial',
             r'\bMin\b': 'Mini', r'\bGig\b': 'Gigante', r'\bPed\b': 'Pedaços', r'\bMol\b': 'Molho',
             r'\bSach\b': 'Sachê', r'\bFrg\b': 'Frango', r'\bVeg\b': 'Vegetais',
             r'\bCord\b': 'Cordeiro', r'\bSalm\b': 'Salmão', r'\bArr\b': 'Arroz', r'\bBat\b': 'Batata'
        }

    def process(self):
        if not os.path.exists(self.file_path):
            return []
        
        # Cache Check
        try:
            mtime = os.path.getmtime(self.file_path)
            if self._cache is not None and self._last_mtime == mtime:
                return self._cache
        except:
            pass

        try:
            # Tenta ler como CSV padrão primeiro
            df = pd.read_csv(self.file_path, nrows=5, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
            if 'SKU' in df.columns and 'Name' in df.columns:
                data = self.process_standard_csv()
            else:
                data = self.process_raw_csv()
            
            # Update Cache
            self._cache = data
            self._last_mtime = mtime
            return data
        except:
            data = self.process_raw_csv()
            self._cache = data
            self._last_mtime = mtime
            return data

    def process_standard_csv(self):
        try:
            df = pd.read_csv(self.file_path, sep=None, engine='python', dtype=str)
            df = df.fillna('')
            
            # Garante colunas
            for col in self.target_columns:
                if col not in df.columns:
                    df[col] = ''
            
            data = df.to_dict(orient='records')
            return self.finalize_data(data)
        except Exception as e:
            print(f"Erro ao processar CSV padrão: {e}")
            return []

    def process_raw_csv(self):
        data = []
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                # Lê todas as linhas
                lines = f.readlines()
                
            # Encontra a linha de cabeçalho
            header_index = -1
            for i, line in enumerate(lines):
                if 'Valor Custo' in line:
                    header_index = i
                    break
            
            if header_index == -1:
                print("Cabeçalho 'Valor Custo' não encontrado")
                return []

            # Processa as linhas a partir do cabeçalho
            # Usa csv reader para lidar com aspas e separadores
            reader = csv.reader(lines[header_index:], delimiter=',')
            rows = list(reader)
            
            if not rows:
                return []

            # Usa a primeira linha para descobrir índices
            header_row = rows[0]
            try:
                # Procura 'Valor Custo' para referência
                idx_custo_header = -1
                for i, col in enumerate(header_row):
                    if 'Valor Custo' in col:
                        idx_custo_header = i
                        break
                
                if idx_custo_header == -1:
                    return []
            except ValueError:
                return []

            # Mapeamento baseado no JS:
            # Assumimos que o SKU está logo após 'Valor Custo'
            start_idx = idx_custo_header + 1
            
            # Verifica se a primeira linha é cabeçalho ou dados
            # Se o valor no start_idx parecer um cabeçalho (ex: "SKU", "Código"), pulamos a linha
            first_val = header_row[start_idx] if len(header_row) > start_idx else ""
            is_header = first_val.lower() in ['sku', 'código', 'codigo', 'code']
            
            start_processing_idx = 1 if is_header else 0
            
            for row in rows[start_processing_idx:]:
                if len(row) < start_idx + 6:
                    continue
                
                # Extrai categoria do departamento se houver
                category = "Geral"
                for col in row:
                    # Procura por "Departamento:" em qualquer parte da string da coluna
                    if 'Departamento' in col and ':' in col:
                        parts = col.split(':', 1)
                        if parts[0].strip() == 'Departamento':
                            category = parts[1].strip()
                            break
                
                sku_raw = row[start_idx]
                desc_raw = row[start_idx + 1]
                stock_raw = row[start_idx + 2]
                price_raw = row[start_idx + 4]
                cost_raw = row[start_idx + 5]
                
                if not sku_raw or not desc_raw:
                    continue

                # Processamento Inteligente
                processed_item = self.create_smart_product(sku_raw, desc_raw, stock_raw, price_raw, cost_raw, category)
                data.append(processed_item)

            return self.finalize_data(data)

        except Exception as e:
            print(f"Erro ao processar CSV bruto: {e}")
            return []

    def create_smart_product(self, sku, name, stock, price, cost, category):
        # Limpeza básica
        sku = str(sku).strip()
        name = str(name).strip()
        
        # Fix Text (Correções de nome)
        name = self.fix_text(name, category)
        category = self.fix_text(category)
        
        # Detecção de Marca e Peso
        brand = self.detect_brand(name)
        weight = self.extract_weight(name)
        
        # Se não detectou marca, tenta usar a categoria se ela parecer uma marca (opcional, mas ajuda visualmente)
        # Mas o usuário pediu para corrigir a categoria, então vamos focar nisso.
        
        # Formatação de Preços
        try:
            price_val = float(price.replace(',', '.'))
        except:
            price_val = 0.0
            
        try:
            cost_val = float(cost.replace(',', '.'))
        except:
            cost_val = 0.0
            
        try:
            stock_val = int(float(stock.replace(',', '.')))
        except:
            stock_val = 0

        # Gera Descrições
        short_desc = self.generate_short_description(name, category, brand)
        full_desc = self.generate_full_description(name, category, price_val, brand, weight)
        
        return {
            'SKU': sku,
            'Name': name,
            'Regular price': f"{price_val:.2f}",
            'Categories': category,
            'Meta: _marca': brand if brand else '',
            'Stock': str(stock_val),
            'Description': full_desc,
            'Short description': short_desc,
            'Weight (kg)': weight if weight else '',
            'Meta: _custo': f"{cost_val:.2f}"
        }

    def fix_text(self, text, category=""):
        if not isinstance(text, str):
            return text
        
        # Aplica substituições regex
        for pattern, replacement in self.replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            
        # Capitalização (Title Case simples)
        if text:
            text = text[0].upper() + text[1:]
            
        return text

    def detect_brand(self, name):
        if not name: return None
        name_lower = name.lower()
        
        # 1. Busca exata/regex
        for key, value in self.marcas_conhecidas.items():
            # Tenta encontrar a marca com word boundaries
            if re.search(r'\b' + re.escape(key) + r'\b', name_lower):
                return value
        
        # 2. Busca relaxada (se não encontrou com boundary)
        # Útil para casos onde a marca está colada em outra palavra ou pontuação estranha
        for key, value in self.marcas_conhecidas.items():
            if key in name_lower:
                # Verifica se não é parte de outra palavra comum (ex: "pet" em "tapete")
                # Mas como as chaves são marcas específicas, o risco é menor.
                # Evita falsos positivos curtos
                if len(key) > 3: 
                    return value
                    
        return None

    def get_product_history(self, sku):
        """Recupera histórico de preços dos backups"""
        history = []
        try:
            backups_dir = os.path.join(os.path.dirname(self.file_path), 'backups')
            if not os.path.exists(backups_dir):
                return []
            
            # Pega os últimos 10 backups
            files = sorted(glob.glob(os.path.join(backups_dir, '*.csv')), reverse=True)[:10]
            
            for file_path in files:
                try:
                    # Extrai data do nome do arquivo (estoque_YYYY-MM-DD_HH-MM-SS.csv)
                    filename = os.path.basename(file_path)
                    date_str = filename.replace('estoque_', '').replace('.csv', '')
                    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
                    formatted_date = date_obj.strftime("%d/%m/%Y")
                    
                    # Lê o arquivo (modo rápido, apenas procurando o SKU)
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                        if sku not in content:
                            continue
                        
                        # Se SKU está no arquivo, precisamos parsear para pegar o preço correto
                        # Para ser rápido, vamos usar regex simples se o formato for conhecido
                        # Mas como o formato muda (raw vs standard), melhor usar uma busca linha a linha
                        f.seek(0)
                        for line in f:
                            if sku in line:
                                # Tenta extrair preço. Assumindo formato raw onde preço é uma das colunas
                                # Isso é frágil, mas rápido. Melhor seria parsear direito se performance permitir.
                                # Vamos tentar parsear a linha como CSV
                                parts = list(csv.reader([line]))[0]
                                # Procura algo que pareça preço (tem vírgula e números)
                                for part in parts:
                                    if re.match(r'^\d+,\d{2}$', part.strip()):
                                        price = part.strip()
                                        history.append({'date': formatted_date, 'price': price})
                                        break
                                break
                except:
                    continue
                    
            return history[::-1] # Retorna cronológico (antigo -> novo)
        except Exception as e:
            print(f"Erro ao buscar histórico: {e}")
            return []

    def extract_weight(self, name):
        if not name: return None
        # Padrões de peso (Ported from JS)
        patterns = [
            r'(\d+(?:[,\.]\d+)?)\s*kg',
            r'(\d+(?:[,\.]\d+)?)\s*k\b',
            r'(\d+)\s*quilos?',
            r'(\d+(?:[,\.]\d+)?)\s*g(?!\w)',
            r'(\d+(?:[,\.]\d+)?)\s*gramas?',
            r'(\d+(?:[,\.]\d+)?)\s*ml',
            r'(\d+(?:[,\.]\d+)?)\s*litros?',
            r'(\d+(?:[,\.]\d+)?)\s*l(?!\w)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                val_str = match.group(1).replace(',', '.')
                try:
                    val = float(val_str)
                    # Conversão para kg
                    if 'g' in pattern and 'kg' not in pattern: # gramas
                        val /= 1000
                    elif 'ml' in pattern: # ml
                        val /= 1000
                    
                    if 0.001 < val <= 50:
                        return f"{val:.3f}"
                except:
                    continue
        return None

    def generate_short_description(self, name, category, brand):
        desc = f"{name}"
        if brand:
            desc += f" | Marca: {brand}"
        desc += f" | Categoria: {category} | AquaFlora Agroshop"
        return desc

    def generate_full_description(self, name, category, price, brand, weight):
        # HTML Description
        intro = "<p>"
        if brand:
            intro += f"Produto <strong>{brand}</strong> da linha {category}. "
        else:
            intro += f"Produto de alta qualidade da categoria {category}. "
        
        intro += "Disponível na <strong>AquaFlora Agroshop</strong> com "
        if weight:
            intro += f"<strong>{weight}kg</strong> e "
        intro += "melhor custo-benefício.</p>"
        
        features = "<ul class='product-features'>"
        if brand:
            features += f"<li>🏷️ <strong>Marca:</strong> {brand}</li>"
        if weight:
            features += f"<li>⚖️ <strong>Peso/Conteúdo:</strong> {weight} Kg</li>"
        features += f"<li>📦 <strong>Categoria:</strong> {category}</li>"
        features += "<li>✅ <strong>Produto Original</strong> com garantia</li>"
        features += "<li>🚚 <strong>Entrega Rápida</strong> para todo o Brasil</li>"
        features += "<li>💳 <strong>Diversas formas de pagamento</strong></li></ul>"
        
        cta = "<div class='cta-section'><p>📞 <strong>Dúvidas?</strong> Nossa equipe está pronta para ajudar!</p><p>⭐ <strong>AquaFlora Agroshop</strong> - Sua loja de confiança!</p></div>"
        
        return f"<div class='product-description'><h2>{name}</h2>{intro}{features}{cta}</div>"

    def finalize_data(self, data):
        # Verifica imagens e ordena
        if self.images_folder:
            for item in data:
                sku = str(item.get('SKU', '')).strip()
                image_path = os.path.join(self.images_folder, f"{sku}.jpg")
                item['has_image'] = os.path.exists(image_path)
        
        # Ordena: Com imagem primeiro, depois por nome
        data.sort(key=lambda x: (not x.get('has_image', False), x.get('Name', '')))
        return data

    def get_stats(self, data):
        if not data:
            return {'total': 0, 'in_stock': 0, 'out_of_stock': 0, 'categories': []}
            
        df = pd.DataFrame(data)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0)
        
        return {
            'total': len(df),
            'in_stock': len(df[df['Stock'] > 0]),
            'out_of_stock': len(df[df['Stock'] <= 0]),
            'categories': sorted(df['Categories'].unique().tolist()) if 'Categories' in df.columns else []
        }

    def get_dashboard_stats(self, data):
        if not data:
            return {}
            
        df = pd.DataFrame(data)
        
        # Conversão numérica
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0)
        
        # Limpa preço (R$ 1.200,50 -> 1200.50)
        def clean_price(p):
            if isinstance(p, str):
                return float(p.replace('.', '').replace(',', '.'))
            return float(p)
            
        df['PriceVal'] = df['Regular price'].apply(clean_price)
        
        # Cálculos
        total_items = len(df)
        total_stock_count = df['Stock'].sum()
        total_value = (df['Stock'] * df['PriceVal']).sum()
        low_stock = len(df[(df['Stock'] > 0) & (df['Stock'] <= 3)])
        out_of_stock = len(df[df['Stock'] <= 0])
        
        # Top Categorias
        top_categories = df['Categories'].value_counts().head(5).to_dict()
        
        return {
            'total_items': int(total_items),
            'total_stock_count': int(total_stock_count),
            'total_value': float(total_value),
            'low_stock': int(low_stock),
            'out_of_stock': int(out_of_stock),
            'top_categories': top_categories
        }
