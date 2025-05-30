import os
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from docx import Document
from langdetect import detect
from deep_translator import GoogleTranslator

# Caminhos
PASTA_ARQUIVOS = "arquivos"
PASTA_SAIDA = "json"
base_conhecimento = []

# Lista de URLs a serem processadas
URLS = [
    "https://lemontechinfo.atlassian.net/wiki/spaces/NEA/pages/1930395681/Gest+o+de+Bilhetes",
    "https://lemontechinfo.atlassian.net/wiki/spaces/NEA/pages/1920434182/Ferramenta+de+Importa+o",
    "https://lemontechinfo.atlassian.net/wiki/spaces/NEC/pages/1855324171/Acessando+SelfBooking",
    "https://lemontechinfo.atlassian.net/wiki/spaces/NEC/pages/2376663042/Solicitando+A+reo+Online"
]

# Função para traduzir texto se estiver em inglês
def traduzir_para_pt(texto):
    try:
        if detect(texto) == "en":
            return GoogleTranslator(source='en', target='pt').translate(texto)
    except:
        pass
    return texto

# Adiciona bloco de conhecimento à base
def adicionar_conteudo(conteudo, fonte):
    conteudo = traduzir_para_pt(conteudo.strip())
    if len(conteudo) > 30:  # evita blocos muito curtos
        base_conhecimento.append({
            "conteudo": conteudo,
            "fonte": fonte
        })

# Processa arquivos .docx
def processar_word(caminho):
    doc = Document(caminho)
    for p in doc.paragraphs:
        texto = p.text.strip()
        if texto:
            adicionar_conteudo(texto, os.path.basename(caminho))

# Processa arquivos .pdf
def processar_pdf(caminho):
    leitor = PdfReader(caminho)
    texto_total = ""
    for pagina in leitor.pages:
        texto_total += pagina.extract_text() + "\n"
    paragrafos = texto_total.split("\n")
    for p in paragrafos:
        texto = p.strip()
        if texto:
            adicionar_conteudo(texto, os.path.basename(caminho))

# Processa arquivos .xlsx (pega todas as células com texto)
def processar_excel(caminho):
    df = pd.read_excel(caminho, dtype=str)
    for _, linha in df.iterrows():
        for valor in linha:
            if pd.notna(valor):
                texto = str(valor).strip()
                if texto:
                    adicionar_conteudo(texto, os.path.basename(caminho))

# Processa páginas da web (URLs)
def processar_url(url):
    try:
        print(f"🌐 Processando URL: {url}")
        resposta = requests.get(url)
        resposta.raise_for_status()
        soup = BeautifulSoup(resposta.text, "html.parser")
        conteudos = soup.find_all(["p", "li"])
        for tag in conteudos:
            texto = tag.get_text(strip=True)
            if texto:
                adicionar_conteudo(texto, url)
    except Exception as e:
        print(f"❌ Erro ao processar {url}: {e}")

# Função principal
def main():
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    # Processa arquivos locais
    for arquivo in os.listdir(PASTA_ARQUIVOS):
        if arquivo.startswith("~$"):
            continue
        caminho = os.path.join(PASTA_ARQUIVOS, arquivo)
        print(f"📂 Processando arquivo: {arquivo}")
        if arquivo.endswith(".docx"):
            processar_word(caminho)
        elif arquivo.endswith(".pdf"):
            processar_pdf(caminho)
        elif arquivo.endswith(".xlsx"):
            processar_excel(caminho)
        else:
            print(f"⚠️ Tipo de arquivo não suportado: {arquivo}")

    # Processa URLs da internet
    for url in URLS:
        processar_url(url)

    # Caminho do arquivo de saída
    caminho_saida = os.path.join(PASTA_SAIDA, "base_semantica.json")
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(base_conhecimento, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Base criada com {len(base_conhecimento)} blocos de conteúdo.")

if __name__ == "__main__":
    main()
