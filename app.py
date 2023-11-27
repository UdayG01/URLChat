
import os
import pinecone
import sys
from langchain.llms import Replicate
from langchain.vectorstores import Pinecone
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.document_loaders import WebBaseLoader

import streamlit as st
from htmlTemplates import css, bot_template, user_template

os.environ['REPLICATE_API_TOKEN'] = "r8_Ql18CMc7pN46DTrx0Qn8IIHK3RCERrH2ZloZX"
pinecone.init(api_key='58da24ae-2fc8-4c12-97a1-9a4d2ff088df', environment='asia-southeast1-gcp-free')

def load_doc(url):
  #loader = WebBaseLoader("https://medium.com/@adeigbesharon/i-fell-in-love-with-your-personality-first-828a7bd22d95")
  loader = WebBaseLoader(url)
  documents = loader.load()
  return documents

def split_text(docs):
  text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
  texts = text_splitter.split_documents(docs)
  return texts

def get_vectorstore(texts):
  embeddings = HuggingFaceEmbeddings()
  index_name = "urlchat"
  index = pinecone.Index(index_name)
  db = Pinecone.from_documents(texts, embeddings, index_name=index_name)
  return db

def get_conversation_chain(db):
  llm = Replicate(
    model="a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5",
    input={"temperature": 0.75, "max_length": 3000}
  )

  memory = ConversationBufferMemory(memory_key = 'chat_history', return_messages=True)
  conversation_chain = ConversationalRetrievalChain.from_llm(
      llm=llm,
      retriever=db.as_retriever(),
      memory=memory
  )
  return conversation_chain


def handle_userinput(user_question):
  response = st.session_state.conversation({'question': user_question})
  st.session_state.chat_history = response['chat_history']

  for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)



def main():
  st.set_page_config(page_title="ChatLLM.ai",
                    page_icon=":robot_face:")
  st.write(css, unsafe_allow_html=True)

  if "conversation" not in st.session_state:
    st.session_state.conversation = None
  if "chat_history" not in st.session_state:
    st.session_state.chat_history = None


  st.header("URLChat :desktop_computer:")
  user_question = st.text_input("What brings you here? ")
  if user_question:
    handle_userinput(user_question)

  with st.sidebar:
    st.subheader("Your URL")
    form = st.form("my_form")
    url = form.text_input("Your URL: ")
    submit = form.form_submit_button("Process")

    if submit:
      with st.spinner("Process"):
        # Perform loading on the url
        docs = load_doc(url)
        # st.write(text)

        # Perform text-splitting
        texts  = split_text(docs)

        # Performing embeddings/vectorization using HuggingFaceEmbeddings
        # and I'll be storing these embeddings in Chroma vector store
        db = get_vectorstore(texts)

        # Making a conversation chain
        # conversation = get_conversation_chain(db)
        # do the below one in case you want a persistent convo
        st.session_state.conversation = get_conversation_chain(db)

if __name__ == '__main__':
  main()
