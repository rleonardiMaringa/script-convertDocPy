import os
import json
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from langdetect import detect
from deep_translator import GoogleTranslator

# Caminhos
PASTA_ARQUIVOS = "arquivos"
PASTA_SAIDA = "json"
base_conhecimento = []

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

# Adiciona pergunta e resposta, com tradução e normalização
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

# Função principal
def main():
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    for arquivo in os.listdir(PASTA_ARQUIVOS):
        if arquivo.startswith("~$"):  # Ignora arquivos temporários do Excel
            continue
        caminho = os.path.join(PASTA_ARQUIVOS, arquivo)
        print(f"🔍 Processando: {arquivo}")
        if arquivo.endswith(".docx"):
            processar_word(caminho)
        elif arquivo.endswith(".pdf"):
            processar_pdf(caminho)
        elif arquivo.endswith(".xlsx"):
            processar_excel(caminho)
        else:
            print(f"⚠️ Tipo de arquivo não suportado: {arquivo}")

    # Caminho do arquivo de saída
    caminho_saida = os.path.join(PASTA_SAIDA, "base_conhecimento.json")
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(base_conhecimento, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Base criada com {len(base_conhecimento)} perguntas.")

if __name__ == "__main__":
    main()
