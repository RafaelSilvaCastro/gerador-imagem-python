import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import math # Para checar valores NaN de forma robusta

# --- Configurações Principais ---
ARQUIVO_EXCEL = 'promocoes.xlsx'
PASTA_IMAGENS_BASE = 'img'
PASTA_SAIDA = 'banners_prontos' 
EXTENSOES_POSSIVEIS = ['jpg', 'jpeg', 'png']
NOME_FONTE = "arialbd.ttf" # Arial Bold para destaque
LOGO_AMAISCICLO_FILE = 'amaisciclo.jpeg' 
IMAGEM_FUNDO_FILE = 'fundo_padrao.jpg'

# --- Configurações do Layout ---
LARGURA_BANNER = 1080
ALTURA_BANNER = 1350 
COR_FUNDO = 'white'

# --- Configurações de Área ---
ALTURA_IMAGEM_PRODUTO_MAX = 650
Y_INICIO_AREA_TEXTO = 1000
LARGURA_MAX_TEXTO = LARGURA_BANNER - 100 

# --- Configurações de Texto e Cores ---
COR_PRECO_DESTAQUE = (200, 0, 0) # Vermelho para o preço promocional
COR_TEXTO_DESCRICAO = (30, 30, 30) 
COR_PRECO_ANTIGO = (150, 150, 150) # Cinza para o preço riscado

PADDING_LATERAL = 150 
TEXT_LINE_SPACING = 20 

# --- CONFIGURAÇÕES DE FONTE ---
TAMANHO_FONTE_DESTAQUE_PRINCIPAL = 100
TAMANHO_FONTE_PRECO_ANTIGO = 55 # Tamanho do preço riscado

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
        # ✅ LEITURA ROBUSTA: Lê código como string e preços como float, garantindo consistência.
        df = pd.read_excel(
            ARQUIVO_EXCEL, 
            dtype={'codigo': str}, # Garantimos que o código é lido como string
            converters={'valor_promocional': float, 'valor_original': float} 
        )
        
        # Normaliza nomes das colunas
        df.columns = df.columns.str.strip().str.lower()
        
        print(f"Planilha '{ARQUIVO_EXCEL}' lida com sucesso. Total de {len(df)} promoções encontradas.")
        
        colunas_necessarias = ['codigo', 'descricao', 'valor_promocional']
        for col in colunas_necessarias:
            if col not in df.columns:
                print(f"ERRO CRÍTICO: Coluna obrigatória '{col}' não encontrada no Excel.")
                return

        if 'valor_original' not in df.columns:
            print("AVISO: Coluna 'valor_original' não encontrada no Excel. Apenas o preço promocional será exibido.")
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
    except IOError:
        print(f"AVISO: Fonte '{NOME_FONTE}' não encontrada. Usando fonte padrão. Tente 'arial.ttf'.")
        fonte_descricao = ImageFont.load_default()
        fonte_valor = ImageFont.load_default()
        fonte_preco_antigo = ImageFont.load_default() 
        fonte_destaque_principal = ImageFont.load_default()


    def desenhar_texto(draw, posicao, texto, fonte, cor):
        draw.text(posicao, texto, font=fonte, fill=cor)

    for index, dados_promo in df.iterrows():
        codigo_produto = None
        try:
            # --- 1. TRATAMENTO ROBUSTO DO CÓDIGO DO PRODUTO (Corrigido) ---
            if pd.notna(dados_promo['codigo']):
                codigo_str = str(dados_promo['codigo']).strip()
                
                # Caso o pandas leia o código como float (ex: '83.0')
                if codigo_str.endswith('.0'):
                    codigo_produto = codigo_str[:-2]
                else:
                    codigo_produto = codigo_str
            else:
                codigo_produto = f"ITEM_{index}"
            
            # Checa se o código está vazio após o tratamento
            if not codigo_produto:
                 print(f"AVISO (Linha {index+2}): Código de produto vazio após tratamento. Pulando.")
                 continue

            descricao_original = str(dados_promo['descricao']).upper().strip()
            
            # --- 2. TRATAMENTO ROBUSTO DOS VALORES (Preço) ---
            valor_float = dados_promo['valor_promocional']
            valor_exibicao = f"R$ {valor_float:.2f}".replace('.', ',')
            
            valor_original_exibicao = None
            valor_original_float = dados_promo.get('valor_original')
            
            # Condição para mostrar o preço antigo: 
            # Deve ser um número válido, maior que zero E maior que o promocional.
            if (
                pd.notna(valor_original_float) and 
                not math.isnan(valor_original_float) and 
                valor_original_float > 0 and 
                valor_original_float > valor_float
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
                # Agora o erro deve indicar exatamente qual código NÃO FOI ENCONTRADO
                print(f"ERRO (Linha {index+2} - Código '{codigo_produto}'): Imagem não encontrada. Verifique se o arquivo '{codigo_produto}.(ext)' existe na pasta '{PASTA_IMAGENS_BASE}'.")
                continue
            
            # --- Criação do Banner e Fundo --- (Mantido)
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
            
            # Colocando a Imagem do Produto e Logo
            img_produto = Image.open(caminho_imagem_base).convert("RGB")
            img_produto.thumbnail((LARGURA_BANNER, ALTURA_IMAGEM_PRODUTO_MAX))
            x_img_centralizada = (LARGURA_BANNER - img_produto.width) // 2
            y_img_centralizada = 300 
            banner_final.paste(img_produto, (x_img_centralizada, y_img_centralizada))
    
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
            
            # 🌟 DESENHA O PREÇO ORIGINAL (RISCADO) 🌟
            if valor_original_exibicao:
                texto_w_antigo, texto_h_antigo = get_text_dimensions(draw, valor_original_exibicao, fonte_preco_antigo)
                
                x_antigo = (LARGURA_BANNER - texto_w_antigo) // 2 
                y_antigo = y_inicio_preco
                
                # Desenha o texto do preço antigo
                desenhar_texto(draw, (x_antigo, y_antigo), valor_original_exibicao, fonte_preco_antigo, COR_PRECO_ANTIGO)
                
                # Desenha a linha de risco
                x_linha1 = x_antigo + 5 
                y_linha = y_antigo + texto_h_antigo // 2
                x_linha2 = x_antigo + texto_w_antigo - 5
                
                draw.line([(x_linha1, y_linha), (x_linha2, y_linha)], fill=COR_PRECO_ANTIGO, width=8)
                
                # Ajusta o Y inicial para o preço promocional ficar abaixo do riscado
                y_inicio_preco += texto_h_antigo + 10 

            # DESENHA O PREÇO PROMOCIONAL (NOVO)
            texto_w_valor, texto_h_valor = get_text_dimensions(draw, valor_exibicao, fonte_valor)
            
            x_valor = (LARGURA_BANNER - texto_w_valor) // 2 
            y_valor = y_inicio_preco
            
            desenhar_texto(draw, (x_valor, y_valor), valor_exibicao, fonte_valor, COR_PRECO_DESTAQUE)
            
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