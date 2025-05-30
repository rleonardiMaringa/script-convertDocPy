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
    # Adicione outras URLs aqui, se quiser
]

# Função para traduzir texto se estiver em inglês
def traduzir_para_pt(texto):
    try:
        if detect(texto) == "en":
            return GoogleTranslator(source='en', target='pt').translate(texto)
    except:
        pass
    return texto

# Converte "yes" e "no" para português
def normalizar_resposta_simples(resposta):
    if resposta.strip().lower() == "yes":
        return "Sim"
    elif resposta.strip().lower() == "no":
        return "Não"
    return resposta

# Adiciona pergunta e resposta formatadas à base
def adicionar_pergunta_resposta(pergunta, resposta):
    pergunta = traduzir_para_pt(pergunta.strip())
    resposta = normalizar_resposta_simples(resposta.strip())
    resposta = traduzir_para_pt(resposta)  # traduz outras respostas se estiverem em inglês
    if pergunta and resposta:
        base_conhecimento.append({"pergunta": pergunta, "resposta": resposta})

# Processa arquivos .docx
def processar_word(caminho):
    doc = Document(caminho)
    pergunta, resposta = "", ""
    for p in doc.paragraphs:
        texto = p.text.strip()
        if not texto:
            continue
        if texto.endswith("?"):
            if pergunta and resposta:
                adicionar_pergunta_resposta(pergunta, resposta)
            pergunta = texto
            resposta = ""
        else:
            resposta += texto + " "
    if pergunta and resposta:
        adicionar_pergunta_resposta(pergunta, resposta)

# Processa arquivos .pdf
def processar_pdf(caminho):
    leitor = PdfReader(caminho)
    texto_total = ""
    for pagina in leitor.pages:
        texto_total += pagina.extract_text() + "\n"
    linhas = texto_total.split("\n")
    pergunta, resposta = "", ""
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        if linha.endswith("?"):
            if pergunta and resposta:
                adicionar_pergunta_resposta(pergunta, resposta)
            pergunta = linha
            resposta = ""
        else:
            resposta += linha + " "
    if pergunta and resposta:
        adicionar_pergunta_resposta(pergunta, resposta)

# Processa arquivos .xlsx
def processar_excel(caminho):
    df = pd.read_excel(caminho)
    for _, linha in df.iterrows():
        pergunta = str(linha.get("pergunta", "")).strip()
        resposta = str(linha.get("resposta", "")).strip()
        if pergunta and resposta:
            adicionar_pergunta_resposta(pergunta, resposta)

# Heurística simples para detectar se é pergunta
def eh_pergunta(texto):
    texto = texto.strip().lower()
    return (
        texto.endswith("?") or
        texto.startswith("como ") or
        texto.startswith("o que ") or
        texto.startswith("por que ") or
        texto.startswith("qual ") or
        texto.startswith("quando ") or
        texto.startswith("quem ")
    )

# Processa páginas da web (URLs)
def processar_url(url):
    try:
        print(f"🌐 Processando URL: {url}")
        resposta = requests.get(url)
        resposta.raise_for_status()
        soup = BeautifulSoup(resposta.text, "html.parser")

        conteudos = soup.find_all(["p", "li", "h2", "h3"])
        bloco = ""

        for tag in conteudos:
            texto = tag.get_text(strip=True)
            if not texto or len(texto) < 10:
                continue
            bloco += texto + " "

        paragrafos = bloco.split(". ")
        adicionados = set()

        for p in paragrafos:
            p = p.strip()
            if len(p) < 30 or p.lower() in adicionados:
                continue
            p_traduzido = traduzir_para_pt(p)
            if eh_pergunta(p_traduzido):
                base_conhecimento.append({
                    "pergunta": p_traduzido,
                    "resposta": f"(Conteúdo extraído da página: {url})"
                })
            else:
                base_conhecimento.append({
                    "conteudo": p_traduzido,
                    "fonte": url
                })
            adicionados.add(p.lower())

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
    caminho_saida = os.path.join(PASTA_SAIDA, "base_qa.json")
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(base_conhecimento, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Base criada com {len(base_conhecimento)} registros.")

if __name__ == "__main__":
    main()
