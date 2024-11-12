import chromadb
import os
from groq import Groq
import streamlit as st

#Configurar a chave de API do Groq
os.environ["GROQ_API_KEY"] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Inicializar o cliente do ChromaDB
chroma_client = chromadb.Client()
chroma_client = chromadb.PersistentClient(path="db")
collection = chroma_client.get_or_create_collection(name="artigo")

# Função para dividir o texto longo em pedaços menores
def quebra_texto(texto, pedaco_tamanho=1000, sobrepor=200):
    if pedaco_tamanho <= sobrepor:
        raise ValueError("pedaco necessita ser maior do que o sobrepor")

    pedacos = []
    inicio = 0
    while inicio < len(texto):
        final = inicio + pedaco_tamanho
        pedacos.append(texto[inicio:final])
        if final >= len(texto):
            inicio = len(texto)
        else:
            inicio += pedaco_tamanho - sobrepor

    return pedacos

# Ler o arquivo de texto
with open("texto.txt", "r", encoding="utf-8") as file:
    texto = file.read()

# Chamando a função dividir o texto em pedaços
pedacos = quebra_texto(texto)

# Adicionar cada pedaço ao ChromaDB
for i, pedaco in enumerate(pedacos):
    print(f"pedaco {i+1}:")
    print(pedaco)
    print(len(pedaco))
    print()

    collection.add(documents=pedaco, ids=[str(i)])

# Prompt para o assistente
prompt = """
Você é um assistente do Restaurante Erik Sabores.
Use o seguinte contexto para responder a questão, não use nenhuma informação adicional, se nao houver informacao no contexto, responda: Desculpe mas não consigo ajudar.
Sempre termine a resposta com: Foi um prazer lhe atender, não deixe de provar nossos sabores.
"""

# Função para consultar o ChromaDB
def consultar_chromadb(questao):
    results = collection.query(query_texts=questao, n_results=2)
    conteudo = results["documents"][0][0] + results["documents"][0][1]
    return conteudo

# Função para gerar resposta usando Groq
def gerar_resposta_groq(prompt, conteudo, questao):
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": prompt},
            {"role": "system", "content": conteudo},
            {"role": "user", "content": questao},
        ],
        model="llama-3.1-70b-versatile",
    )
    return chat_completion.choices[0].message.content

# Configurar o Streamlit
st.title("Assistente do Restaurante Erik Sabores")
st.write("Você pode fazer perguntas ao nosso assistente. Ele usará o contexto fornecido para responder.")

# Entrada do usuário
questao = st.text_input("Digite sua pergunta:")

# Botão para processar a pergunta
if st.button("Perguntar"):
    if questao:

        # Consultar ChromaDB
        conteudo = consultar_chromadb(questao)

        # Gerar resposta com Groq
        try:
            resposta = gerar_resposta_groq(prompt, conteudo, questao)
            st.write("Resposta do assistente:")
            st.write(resposta)
        except AttributeError as e:
            st.error(f"Erro: {e}")
            st.info("Verifique a documentação do Groq para os métodos corretos.")
    else:
        st.write("Por favor, digite uma pergunta.")
