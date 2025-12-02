import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import math # Para checar valores NaN de forma robusta

# --- Configurações Principais ---
ARQUIVO_EXCEL = 'promocoes.xlsx'
PASTA_IMAGENS_BASE = 'img'
PASTA_SAIDA = 'banners_prontos_avista' 
EXTENSOES_POSSIVEIS = ['jpg', 'jpeg', 'png']
NOME_FONTE = "arialbd.ttf" # Arial Bold para destaque
LOGO_AMAISCICLO_FILE = 'amaisciclo.jpeg' 
IMAGEM_FUNDO_FILE = 'fundo_padrao.jpg'

# --- Configurações do Layout ---
LARGURA_BANNER = 1080
ALTURA_BANNER = 1350 
COR_FUNDO = 'white'

# --- Configurações de Área ---
# VAI SER SUBSTITUÍDO PELA LARGURA/ALTURA FIXA
# ALTURA_IMAGEM_PRODUTO_MAX = 650 

# NOVO: Tamanho fixo da área do produto (por exemplo, 600x600)
LARGURA_IMAGEM_FIXA = 600
ALTURA_IMAGEM_FIXA = 600

Y_INICIO_AREA_TEXTO = 1000
LARGURA_MAX_TEXTO = LARGURA_BANNER - 100 

# --- Configurações de Texto e Cores ---
COR_PRECO_DESTAQUE = (200, 0, 0) # Vermelho para o preço promocional e 'À VISTA'
COR_TEXTO_DESCRICAO = (30, 30, 30) 
COR_PRECO_ANTIGO = (150, 150, 150) # Cinza para o preço (agora 'A PRAZO')
COR_A_PRAZO = (100, 100, 100) # NOVO: Cor mais suave para 'A PRAZO'

PADDING_LATERAL = 150 
TEXT_LINE_SPACING = 20 

# --- CONFIGURAÇÕES DE FONTE ---
TAMANHO_FONTE_DESTAQUE_PRINCIPAL = 100
TAMANHO_FONTE_PRECO_ANTIGO = 55 # Tamanho do preço 'A PRAZO' (Não mais riscado)
TAMANHO_FONTE_A_VISTA = 50 # Tamanho para o texto 'À VISTA'
TAMANHO_FONTE_A_PRAZO = 40 # NOVO: Tamanho para o texto 'A PRAZO'

# --- Configuração Adicional para o Bloco de Preço ---
TEXTO_A_VISTA = "À VISTA"
TEXTO_A_PRAZO = "A PRAZO"
SPACER_PRECO_AVISTA = 20 # Espaçamento entre o preço e o texto 'À VISTA'
SPACER_PRECO_APRAZO = 15 # NOVO: Espaçamento para o texto 'A PRAZO'


# --- Funções Auxiliais ---
def get_text_dimensions(draw, text_string, font):
    """Retorna a largura e altura do texto usando draw.textbbox"""
    bbox = draw.textbbox((0, 0), text_string, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height

def wrap_text_to_fit(draw, text, font, max_width):
    """Quebra uma string em uma lista de strings para que caibam na largura máxima."""
    words = text.split(' ')
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " " if current_line else word
        test_width, _ = get_text_dimensions(draw, test_line.strip(), font)
        
        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "
            
    lines.append(current_line.strip())
    return lines

def colar_logo(banner, logo_path, max_height, x_pos, y_pos):
    """Carrega o logo, redimensiona e cola no banner."""
    if not os.path.exists(logo_path):
        print(f"AVISO CRÍTICO: Arquivo de logo '{logo_path}' não encontrado no caminho do script.")
        return

    try:
        logo = Image.open(logo_path).convert("RGBA")
        largura_original, altura_original = logo.size
        # Mantém a proporção ao redimensionar para a altura máxima
        nova_largura = int(largura_original * (max_height / altura_original))
        logo = logo.resize((nova_largura, max_height))
        # O logo precisa ser colado com o próprio logo como máscara (o 4º argumento) para transparência
        banner.paste(logo, (x_pos, y_pos), logo)
    except Exception as e:
        print(f"AVISO: Erro ao processar o logo: {e}")


# --- Função Principal ---
def criar_banners_em_lote():
    if not os.path.exists(PASTA_SAIDA):
        os.makedirs(PASTA_SAIDA)
    
    try:
        df = pd.read_excel(
            ARQUIVO_EXCEL, 
            dtype={'codigo': str}, 
            converters={'valor_promocional': float, 'valor_original': float} 
        )
        
        df.columns = df.columns.str.strip().str.lower()
        
        print(f"Planilha '{ARQUIVO_EXCEL}' lida com sucesso. Total de {len(df)} promoções encontradas.")
        
        colunas_necessarias = ['codigo', 'descricao', 'valor_promocional']
        for col in colunas_necessarias:
            if col not in df.columns:
                print(f"ERRO CRÍTICO: Coluna obrigatória '{col}' não encontrada no Excel.")
                return

        if 'valor_original' not in df.columns:
            print("AVISO: Coluna 'valor_original' não encontrada no Excel. Apenas o preço promocional (À VISTA) será exibido.")
            df['valor_original'] = None 
            
    except Exception as e:
        print(f"ERRO ao ler o Excel: Certifique-se que o arquivo '{ARQUIVO_EXCEL}' existe. Detalhe: {e}")
        return

    try:
        font_path = NOME_FONTE
        fonte_descricao = ImageFont.truetype(font_path, 45) 
        fonte_valor = ImageFont.truetype(font_path, 100) 
        fonte_preco_antigo = ImageFont.truetype(font_path, TAMANHO_FONTE_PRECO_ANTIGO) 
        fonte_destaque_principal = ImageFont.truetype(font_path, TAMANHO_FONTE_DESTAQUE_PRINCIPAL)
        fonte_a_vista = ImageFont.truetype(font_path, TAMANHO_FONTE_A_VISTA)
        # NOVO: Fonte para o "A PRAZO"
        fonte_a_prazo = ImageFont.truetype(font_path, TAMANHO_FONTE_A_PRAZO) 
    except IOError:
        print(f"AVISO: Fonte '{NOME_FONTE}' não encontrada. Usando fonte padrão. Tente 'arial.ttf'.")
        fonte_descricao = ImageFont.load_default()
        fonte_valor = ImageFont.load_default()
        fonte_preco_antigo = ImageFont.load_default() 
        fonte_destaque_principal = ImageFont.load_default()
        fonte_a_vista = ImageFont.load_default()
        # NOVO: Fonte para o "A PRAZO"
        fonte_a_prazo = ImageFont.load_default()


    def desenhar_texto(draw, posicao, texto, fonte, cor):
        draw.text(posicao, texto, font=fonte, fill=cor)

    for index, dados_promo in df.iterrows():
        codigo_produto = None
        try:
            # --- 1. TRATAMENTO ROBUSTO DO CÓDIGO DO PRODUTO ---
            if pd.notna(dados_promo['codigo']):
                codigo_str = str(dados_promo['codigo']).strip()
                if codigo_str.endswith('.0'):
                    codigo_produto = codigo_str[:-2]
                else:
                    codigo_produto = codigo_str
            else:
                codigo_produto = f"ITEM_{index}"
            
            if not codigo_produto:
                print(f"AVISO (Linha {index+2}): Código de produto vazio após tratamento. Pulando.")
                continue

            descricao_original = str(dados_promo['descricao']).upper().strip()
            
            # --- 2. TRATAMENTO ROBUSTO DOS VALORES (Preço) ---
            valor_float = dados_promo['valor_promocional']
            valor_exibicao = f"R$ {valor_float:.2f}".replace('.', ',')
            
            valor_original_exibicao = None
            valor_original_float = dados_promo.get('valor_original')
            
            # Condição para mostrar o preço 'A PRAZO'
            if (
                pd.notna(valor_original_float) and 
                not math.isnan(valor_original_float) and 
                valor_original_float > 0 # Agora não precisa ser maior que o promocional
            ):
                valor_original_exibicao = f"R$ {valor_original_float:.2f}".replace('.', ',')
            
            # --- 3. BUSCA ROBUSTA DA IMAGEM ---
            caminho_imagem_base = None
            for ext in EXTENSOES_POSSIVEIS:
                nome_tentativa = f"{codigo_produto}.{ext}"
                caminho_tentativa = os.path.join(PASTA_IMAGENS_BASE, nome_tentativa)
                if os.path.exists(caminho_tentativa):
                    caminho_imagem_base = caminho_tentativa
                    break 
                    
            if caminho_imagem_base is None:
                print(f"ERRO (Linha {index+2} - Código '{codigo_produto}'): Imagem não encontrada. Verifique se o arquivo '{codigo_produto}.(ext)' existe na pasta '{PASTA_IMAGENS_BASE}'.")
                continue
            
            # --- Criação do Banner e Fundo ---
            banner_final = None
            try:
                img_fundo = Image.open(IMAGEM_FUNDO_FILE).convert("RGB")
                proporcao_banner = LARGURA_BANNER / ALTURA_BANNER
                proporcao_fundo = img_fundo.width / img_fundo.height
                
                if proporcao_fundo > proporcao_banner:
                    nova_altura = ALTURA_BANNER
                    nova_largura = int(img_fundo.width * (nova_altura / img_fundo.height))
                    img_fundo = img_fundo.resize((nova_largura, nova_altura))
                    x_corte = (nova_largura - LARGURA_BANNER) // 2
                    img_fundo = img_fundo.crop((x_corte, 0, x_corte + LARGURA_BANNER, ALTURA_BANNER))
                else:
                    nova_largura = LARGURA_BANNER
                    nova_altura = int(img_fundo.height * (nova_largura / img_fundo.width))
                    img_fundo = img_fundo.resize((nova_largura, nova_altura))
                    y_corte = (nova_altura - ALTURA_BANNER) // 2
                    img_fundo = img_fundo.crop((0, y_corte, LARGURA_BANNER, y_corte + ALTURA_BANNER))
                    
                banner_final = img_fundo.copy()

            except FileNotFoundError:
                banner_final = Image.new('RGB', (LARGURA_BANNER, ALTURA_BANNER), color=COR_FUNDO)
            except Exception:
                banner_final = Image.new('RGB', (LARGURA_BANNER, ALTURA_BANNER), color=COR_FUNDO)


            draw = ImageDraw.Draw(banner_final)
            
            # 🌟 NOVA LÓGICA: Colocando a Imagem do Produto em uma Área de Tamanho Fixo 🌟
            
            # 1. Cria uma área de imagem temporária, de tamanho fixo (600x600), com fundo branco para enquadramento
            area_produto_fixa = Image.new('RGB', (LARGURA_IMAGEM_FIXA, ALTURA_IMAGEM_FIXA), color='white')
            
            # 2. Abre a imagem do produto
            img_produto_original = Image.open(caminho_imagem_base).convert("RGB")
            
            # 3. Redimensiona a imagem do produto para que caiba DENTRO da área fixa, mantendo a proporção (thumbnail)
            # Isso garante que a imagem não seja distorcida, mas ainda é limitada ao tamanho da área.
            img_produto_original.thumbnail((LARGURA_IMAGEM_FIXA, ALTURA_IMAGEM_FIXA))
            
            # 4. Centraliza a imagem redimensionada na área fixa (preenchendo com branco o espaço restante)
            x_central_produto = (LARGURA_IMAGEM_FIXA - img_produto_original.width) // 2
            y_central_produto = (ALTURA_IMAGEM_FIXA - img_produto_original.height) // 2
            
            area_produto_fixa.paste(img_produto_original, (x_central_produto, y_central_produto))
            
            # 5. Cola a área fixa (agora com o produto dentro) no banner
            x_final_centralizado = (LARGURA_BANNER - LARGURA_IMAGEM_FIXA) // 2
            y_final_centralizado = 300 # Posição Y onde você quer que a área de 600x600 comece
            
            banner_final.paste(area_produto_fixa, (x_final_centralizado, y_final_centralizado))
            # ----------------------------------------------------------------------------------
    
            colar_logo(
                banner_final, 
                LOGO_AMAISCICLO_FILE, 
                max_height=250,
                x_pos=PADDING_LATERAL, 
                y_pos=60
            )
            
            # --- Área de Descrição e Preço (Rodapé) ---
            linhas_descricao = wrap_text_to_fit(draw, descricao_original, fonte_descricao, LARGURA_MAX_TEXTO)
            
            current_y = Y_INICIO_AREA_TEXTO
            
            # Desenha a descrição
            for line in linhas_descricao:
                line_w, line_h = get_text_dimensions(draw, line, fonte_descricao)
                x_descricao = (LARGURA_BANNER - line_w) // 2 
                desenhar_texto(draw, (x_descricao, current_y), line, fonte_descricao, COR_TEXTO_DESCRICAO)
                current_y += line_h + TEXT_LINE_SPACING
            
            y_inicio_preco = current_y + 30 
            
            # 🌟 DESENHA O PREÇO "A PRAZO" (SEM RISCO) 🌟
            if valor_original_exibicao:
                texto_w_antigo, texto_h_antigo = get_text_dimensions(draw, valor_original_exibicao, fonte_preco_antigo)
                texto_w_ap, texto_h_ap = get_text_dimensions(draw, TEXTO_A_PRAZO, fonte_a_prazo)
                
                # 1. Largura total do bloco A PRAZO (Preço + Espaço + A PRAZO)
                largura_total_bloco_ap = texto_w_antigo + SPACER_PRECO_APRAZO + texto_w_ap
                
                # 2. Posição X inicial para centralizar o bloco inteiro A PRAZO
                x_bloco_ap_inicio = (LARGURA_BANNER - largura_total_bloco_ap) // 2
                y_antigo = y_inicio_preco
                
                # --- DESENHA O PREÇO A PRAZO ---
                x_antigo = x_bloco_ap_inicio
                desenhar_texto(draw, (x_antigo, y_antigo), valor_original_exibicao, fonte_preco_antigo, COR_PRECO_ANTIGO)
                
                # --- DESENHA O "A PRAZO" ---
                x_ap = x_antigo + texto_w_antigo + SPACER_PRECO_APRAZO
                # Centraliza o "A PRAZO" verticalmente com o preço (usando a altura do texto do preço)
                y_ap = y_antigo + (texto_h_antigo - texto_h_ap) - 5 
                
                desenhar_texto(draw, (x_ap, y_ap), TEXTO_A_PRAZO, fonte_a_prazo, COR_A_PRAZO)
                
                # Ajusta o Y inicial para o preço promocional ficar abaixo
                y_inicio_preco += texto_h_antigo + 10 

            # 🌟 DESENHA O PREÇO PROMOCIONAL (NOVO) E O "À VISTA" 🌟
            texto_w_valor, texto_h_valor = get_text_dimensions(draw, valor_exibicao, fonte_valor)
            texto_w_av, texto_h_av = get_text_dimensions(draw, TEXTO_A_VISTA, fonte_a_vista)

            # 1. Largura total do bloco À VISTA (Preço + Espaço + À VISTA)
            largura_total_bloco = texto_w_valor + SPACER_PRECO_AVISTA + texto_w_av

            # 2. Posição X inicial para centralizar o bloco inteiro
            x_bloco_inicio = (LARGURA_BANNER - largura_total_bloco) // 2

            # 3. Posição Y inicial (mantida de acordo com o cálculo anterior)
            y_valor = y_inicio_preco

            # --- DESENHA O PREÇO ---
            x_valor = x_bloco_inicio 
            desenhar_texto(draw, (x_valor, y_valor), valor_exibicao, fonte_valor, COR_PRECO_DESTAQUE)

            # --- DESENHA O "À VISTA" ---
            x_av = x_valor + texto_w_valor + SPACER_PRECO_AVISTA
            # Centraliza o "À VISTA" verticalmente com o preço em destaque
            y_av = y_valor + (texto_h_valor - texto_h_av) - 10 

            desenhar_texto(draw, (x_av, y_av), TEXTO_A_VISTA, fonte_a_vista, COR_PRECO_DESTAQUE)
            
            # Salvando o Banner
            caminho_saida = os.path.join(PASTA_SAIDA, f"banner_{codigo_produto}.png")
            banner_final.save(caminho_saida)
            
            print(f"Banner criado: banner_{codigo_produto}.png")
        
        except Exception as e:
            print(f"ERRO CRÍTICO no processamento do código {codigo_produto} (Linha {index+2}): {e}")

    print("\nProcessamento de Banners concluído!")

# Executa a função
if __name__ == "__main__":
    criar_banners_em_lote()