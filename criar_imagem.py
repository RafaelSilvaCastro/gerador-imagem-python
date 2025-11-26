import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os

# --- Configurações Principais ---
ARQUIVO_EXCEL = 'promocoes.xlsx'
PASTA_IMAGENS_BASE = 'img'
PASTA_SAIDA = 'banners_prontos' 
EXTENSOES_POSSIVEIS = ['jpg', 'jpeg', 'png']
NOME_FONTE = "arialbd.ttf" # Arial Bold para destaque
LOGO_AMAISCICLO_FILE = 'amaisciclo.jpeg' 

# --- Configurações do Layout ---
LARGURA_BANNER = 1080
ALTURA_BANNER = 1350 
COR_FUNDO = 'white'

# --- Configurações de Área ---
ALTURA_IMAGEM_PRODUTO_MAX = 1050 
Y_INICIO_AREA_TEXTO = 1050
LARGURA_MAX_TEXTO = LARGURA_BANNER - 120 

# --- Configurações de Texto e Cores ---
COR_PRECO_DESTAQUE = (200, 0, 0) 
COR_TEXTO_DESCRICAO = (30, 30, 30) 

PADDING_LATERAL = 60 
TEXT_LINE_SPACING = 20 

# --- CONFIGURAÇÕES PARA O BANNER DE DESTAQUE "PROMOÇÃO" ---
TEXTO_BANNER_DESTAQUE_PRINCIPAL = "PROMOÇÃO"
COR_BANNER_DESTAQUE_PRINCIPAL = (255, 204, 0) # Amarelo vibrante
COR_TEXTO_BANNER_DESTAQUE = 'black'

ALTURA_DESTAQUE_PRINCIPAL = 100
# ⬇️ POSIÇÕES AJUSTADAS para o banner de destaque
POS_X_DESTAQUE = 200 # Posição X inicial do banner principal (amarelo)
POS_Y_DESTAQUE = 180 # Posição Y inicial do banner principal (amarelo) 
TAMANHO_FONTE_DESTAQUE_PRINCIPAL = 100

# --- Funções Auxiliares ---
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

# --- FUNÇÃO: Colar o Logo de Imagem ---
def colar_logo(banner, logo_path, max_height, x_pos, y_pos):
    """Carrega o logo, redimensiona e cola no banner."""
    if not os.path.exists(logo_path):
        print(f"AVISO CRÍTICO: Arquivo de logo '{logo_path}' não encontrado no caminho do script.")
        return

    try:
        logo = Image.open(logo_path).convert("RGBA")
        largura_original, altura_original = logo.size
        nova_largura = int(largura_original * (max_height / altura_original))
        logo = logo.resize((nova_largura, max_height))
        banner.paste(logo, (x_pos, y_pos), logo)
    except Exception as e:
        print(f"AVISO: Erro ao processar o logo: {e}")


# --- Função Principal ---
def criar_banners_em_lote():
    if not os.path.exists(PASTA_SAIDA):
        os.makedirs(PASTA_SAIDA)
    
    try:
        df = pd.read_excel(ARQUIVO_EXCEL, dtype={'codigo': str})
        print(f"Planilha '{ARQUIVO_EXCEL}' lida com sucesso. Total de {len(df)} promoções encontradas.")
    except Exception as e:
        print(f"ERRO ao ler o Excel: Certifique-se que o arquivo '{ARQUIVO_EXCEL}' existe. Detalhe: {e}")
        return

    try:
        font_path = NOME_FONTE
        fonte_descricao = ImageFont.truetype(font_path, 50) 
        fonte_valor = ImageFont.truetype(font_path, 100) 
        # Fontes para os banners de destaque
        fonte_destaque_principal = ImageFont.truetype(font_path, TAMANHO_FONTE_DESTAQUE_PRINCIPAL)
    except IOError:
        print(f"AVISO: Fonte '{NOME_FONTE}' não encontrada. Usando fonte padrão. Tente 'arial.ttf'.")
        fonte_descricao = ImageFont.load_default()
        fonte_valor = ImageFont.load_default()
        fonte_destaque_principal = ImageFont.load_default()


    def desenhar_texto(draw, posicao, texto, fonte, cor):
        draw.text(posicao, texto, font=fonte, fill=cor)

    for index, dados_promo in df.iterrows():
        codigo_produto = None
        try:
            if pd.notna(dados_promo['codigo']):
                codigo_produto = str(dados_promo['codigo']).replace(',', '.') 
            else:
                codigo_produto = f"ITEM_{index}"

            descricao_original = str(dados_promo['descricao']).upper().strip()
            valor_float = dados_promo['valor_promocional']
            valor_exibicao = f"R$ {valor_float:.2f}".replace('.', ',')
            
            caminho_imagem_base = None
            for ext in EXTENSOES_POSSIVEIS:
                nome_tentativa = f"{codigo_produto}.{ext}"
                caminho_tentativa = os.path.join(PASTA_IMAGENS_BASE, nome_tentativa)
                if os.path.exists(caminho_tentativa):
                    caminho_imagem_base = caminho_tentativa
                    break 
                    
            if caminho_imagem_base is None:
                print(f"ERRO (Linha {index+2} - Código {codigo_produto}): Imagem não encontrada.")
                continue
            
            banner_final = Image.new('RGB', (LARGURA_BANNER, ALTURA_BANNER), color=COR_FUNDO)
            draw = ImageDraw.Draw(banner_final)
            
            # 6. Colocando a Imagem do Produto
            img_produto = Image.open(caminho_imagem_base).convert("RGB")
            img_produto.thumbnail((LARGURA_BANNER, ALTURA_IMAGEM_PRODUTO_MAX))
            x_img_centralizada = (LARGURA_BANNER - img_produto.width) // 2
            # ⬆️ CORREÇÃO PRINCIPAL AQUI: Mais espaço no topo para a logo
            y_img_centralizada = 300 
            banner_final.paste(img_produto, (x_img_centralizada, y_img_centralizada))
            
            # 7. Colocando o Logo de Imagem (Canto Superior Esquerdo)
            # ⬇️ y_pos mantido para aparecer no topo, agora não será mais coberto
            colar_logo(
                banner_final, 
                LOGO_AMAISCICLO_FILE, 
                max_height=100,  
                x_pos=PADDING_LATERAL, 
                y_pos=40
            )

            # --- Desenha o Banner de Destaque "PROMOÇÃO" ---
            # ⬇️ POSIÇÕES AJUSTADAS para o banner de destaque, para não colidir com o logo
            text_promo_w, text_promo_h = get_text_dimensions(draw, TEXTO_BANNER_DESTAQUE_PRINCIPAL, fonte_destaque_principal)
            
            x1_amarelo = POS_X_DESTAQUE
            y1_amarelo = POS_Y_DESTAQUE
            x2_amarelo = x1_amarelo + text_promo_w + 60 
            y2_amarelo = y1_amarelo + ALTURA_DESTAQUE_PRINCIPAL
            
            draw.rounded_rectangle(
                (x1_amarelo, y1_amarelo, x2_amarelo, y2_amarelo),
                radius=20, 
                fill=COR_BANNER_DESTAQUE_PRINCIPAL
            )
            
            x_text_promo = x1_amarelo + (x2_amarelo - x1_amarelo - text_promo_w) // 2
            y_text_promo = y1_amarelo + (ALTURA_DESTAQUE_PRINCIPAL - text_promo_h) // 2
            desenhar_texto(draw, (x_text_promo, y_text_promo), TEXTO_BANNER_DESTAQUE_PRINCIPAL, fonte_destaque_principal, COR_TEXTO_BANNER_DESTAQUE)

            # --- 8. Área de Descrição e Preço (Rodapé) ---
            linhas_descricao = wrap_text_to_fit(draw, descricao_original, fonte_descricao, LARGURA_MAX_TEXTO)
            
            current_y = Y_INICIO_AREA_TEXTO
            
            for line in linhas_descricao:
                line_w, line_h = get_text_dimensions(draw, line, fonte_descricao)
                x_descricao = (LARGURA_BANNER - line_w) // 2 
                desenhar_texto(draw, (x_descricao, current_y), line, fonte_descricao, COR_TEXTO_DESCRICAO)
                current_y += line_h + TEXT_LINE_SPACING
            
            y_inicio_preco = current_y + 10 

            texto_w_valor, texto_h_valor = get_text_dimensions(draw, valor_exibicao, fonte_valor)
            
            x_valor = (LARGURA_BANNER - texto_w_valor) // 2 
            y_valor = y_inicio_preco
            
            desenhar_texto(draw, (x_valor, y_valor), valor_exibicao, fonte_valor, COR_PRECO_DESTAQUE)
            
            # 9. Salvando o Banner
            caminho_saida = os.path.join(PASTA_SAIDA, f"banner_{codigo_produto}.png")
            banner_final.save(caminho_saida)
            
            print(f"Banner criado: banner_{codigo_produto}.png")
        
        except Exception as e:
            print(f"ERRO CRÍTICO no processamento do código {codigo_produto} (Linha {index+2}): {e}")

    print("\nProcessamento de Banners concluído!")

# Executa a função
if __name__ == "__main__":
    criar_banners_em_lote()