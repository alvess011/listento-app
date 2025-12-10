import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time 
import logging

# --- CONFIGURAÇÃO MANUAL DA CHAVE (SOLUÇÃO TEMPORÁRIA) ---
# Estamos forçando a chave aqui para garantir que funcione
CHAVE_MESTRA = "AIzaSyCnbSkYAcX3XJrdCk9-tfvUJd0CVgXd2v4"

# Configuração de LOGS
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Listento", page_icon="🎧", layout="centered", initial_sidebar_state="collapsed")

# CSS e Estilos
st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 12px; height: 55px; background-color: #FF4B4B; color: white;}
    .error-box {padding: 15px; border-radius: 8px; background-color: #3d1212; border: 1px solid #ff4b4b; color: #ffcccc; margin-top: 10px;}
    </style>
    """, unsafe_allow_html=True)

st.title("🎧 Listento (Modo Teste Direto)")

# --- FORÇAR AUTENTICAÇÃO ---
genai.configure(api_key=CHAVE_MESTRA)
st.toast("✅ Chave Mestra Ativada", icon="🔓")

tab_audio, tab_text = st.tabs(["👂 Ouvir", "📖 Ler"])

with tab_audio:
    target_lang = st.selectbox("Traduzir áudio para:", ["Português (Brasil)", "Inglês", "Espanhol"])
    uploaded_file = st.file_uploader("Arquivo de áudio/vídeo", type=['mp3', 'wav', 'mp4', 'm4a', 'ogg'])
    
    if uploaded_file and st.button("Transcrever Agora"):
        try:
            with st.spinner('Enviando para o Google...'):
                # Salvar temporário
                suffix = os.path.splitext(uploaded_file.name)[1] or ".mp3"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                # Upload
                google_file = genai.upload_file(path=tmp_path)
                
                # Esperar processamento
                while google_file.state.name == "PROCESSING":
                    time.sleep(2)
                    google_file = genai.get_file(google_file.name)

                if google_file.state.name == "FAILED":
                    raise ValueError("Falha no processamento do Google.")

                # Gerar
                model = genai.GenerativeModel('gemini-2.0-flash')
                response = model.generate_content([f"Transcreva e traduza para {target_lang}", google_file])
                
                st.success("Sucesso!")
                st.markdown(response.text)
                os.unlink(tmp_path)

        except Exception as e:
            st.error(f"ERRO: {e}")
            if "429" in str(e):
                st.markdown("<div class='error-box'>COTA ATINGIDA. Espere 2 minutos.</div>", unsafe_allow_html=True)
