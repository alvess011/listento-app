import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time
import logging

# --- Configuração de LOGS ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuração da Página ---
st.set_page_config(
    page_title="Listento",
    page_icon="🎧",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS INTELIGENTE ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 800px;
    }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 55px; font-weight: bold; font-size: 18px;
        background-color: #FF4B4B; color: white; border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2); transition: transform 0.1s;
    }
    .stButton>button:active { transform: scale(0.98); }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; padding-bottom: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 45px; background-color: #262730; border: 1px solid #444; color: #e0e0e0;
        border-radius: 8px; padding: 0px 10px; flex: 1; font-size: 14px;
        display: flex; align-items: center; justify-content: center;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF4B4B !important; color: white !important;
        border: 1px solid #FF4B4B !important; font-weight: bold;
    }
    .error-box {
        padding: 15px; border-radius: 8px; background-color: #3d1212; border: 1px solid #ff4b4b; color: #ffcccc; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GERENCIAMENTO DE CHAVES ---
# Tenta pegar dos segredos do Streamlit, senão usa a sessão
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif "api_key" in st.session_state:
    api_key = st.session_state.api_key

# --- Cabeçalho ---
st.title("🎧 Listento")

# --- LOGIN (Se não houver chave configurada) ---
if not api_key:
    st.info("🔒 Configuração Inicial")
    st.markdown("O sistema não encontrou uma chave configurada nos Secrets.")
    key_input = st.text_input("Insira sua API Key do Google AI Studio:", type="password")
    if key_input:
        st.session_state.api_key = key_input
        st.rerun()
    st.stop()

# ==========================================
# 📱 APP PRINCIPAL
# ==========================================
tab_audio, tab_text, tab_reply, tab_feedback = st.tabs(["👂 Ouvir", "📖 Ler", "✍️ Responder", "📢 Feedback"])

# --- ABA 1: OUVIR ---
with tab_audio:
    target_lang = st.selectbox("Traduzir áudio para:", ["Português (Brasil)", "Inglês", "Espanhol", "Francês", "Italiano", "Alemão"])
    uploaded_file = st.file_uploader("Escolher arquivo", type=['mp3', 'wav', 'ogg', 'm4a', 'mp4', 'mpeg', 'webm', 'mov'], label_visibility="collapsed")
    
    if uploaded_file:
        if uploaded_file.type.startswith('video'):
            st.video(uploaded_file)
        else:
            st.audio(uploaded_file)
        
        if st.button("Transcrever e Traduzir", key="btn_audio"):
            try:
                genai.configure(api_key=api_key)
                
                # Salvar temporário
                file_extension = os.path.splitext(uploaded_file.name)[1] or ".mp3"
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                # Upload e Processamento
                with st.spinner('📤 Enviando para o Google...'):
                    google_file = genai.upload_file(path=tmp_path)
                
                with st.spinner('⚙️ Processando (isso pode levar alguns segundos)...'):
                    # Polling para garantir que o arquivo está pronto
                    while google_file.state.name == "PROCESSING":
                        time.sleep(2)
                        google_file = genai.get_file(google_file.name)
                    
                    if google_file.state.name == "FAILED":
                        raise ValueError("O Google falhou ao processar este arquivo.")

                # Geração
                with st.spinner('🧠 Traduzindo...'):
                    prompt = f"""
                    Atue como um transcritor expert.
                    TAREFA:
                    1. Transcreva TUDO o que for falado.
                    2. Traduza para: {target_lang}.
                    3. Adicione notas de contexto se houver gírias ou termos técnicos.
                    """
                    model = genai.GenerativeModel('gemini-2.0-flash') 
                    response = model.generate_content([prompt, google_file])
                    
                    st.success("Concluído!")
                    st.markdown(response.text)
                
                os.unlink(tmp_path) # Limpar temp

            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "quota" in err_msg.lower():
                    st.markdown("""
                        <div class="error-box">
                            <b>⚠️ Limite Atingido (Erro 429)</b><br>
                            Sua chave atual estourou a cota gratuita ou você clicou muito rápido.<br>
                            1. Espere 2 minutos e tente de novo.<br>
                            2. Gere uma nova chave com <b>outro e-mail Google</b>.
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"Erro técnico: {e}")

# --- ABA 2: LER ---
with tab_text:
    target_lang_text = st.selectbox("Traduzir texto para:", ["Português (Brasil)", "Inglês", "Espanhol"], key="lang_text")
    client_text = st.text_area("Texto do cliente:", height=150, placeholder="Cole o texto aqui")
    
    if st.button("Traduzir Texto", key="btn_text"):
        if not client_text: st.warning("Cole texto primeiro.")
        else:
            with st.spinner('Traduzindo...'):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    response = model.generate_content(f"Traduza para {target_lang_text}: {client_text}")
                    st.markdown(response.text)
                except Exception as e:
                    if "429" in str(e): st.error("⚠️ Cota excedida.")
                    else: st.error(f"Erro: {e}")

# --- ABA 3: RESPONDER ---
with tab_reply:
    target_lang_reply = st.selectbox("Traduzir resposta para:", ["Inglês", "Espanhol", "Francês"])
    my_reply = st.text_area("Sua resposta em Português:", height=150)
    
    if st.button("✨ Gerar Resposta", key="btn_reply"):
        if not my_reply: st.warning("Escreva algo.")
        else:
            with st.spinner('Gerando...'):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    response = model.generate_content(f"Traduza '{my_reply}' para {target_lang_reply}. Mantenha tom profissional.")
                    st.code(response.text, language=None)
                except Exception as e:
                    if "429" in str(e): st.error("⚠️ Cota excedida.")
                    else: st.error(f"Erro: {e}")

# --- ABA 4: FEEDBACK ---
with tab_feedback:
    st.info("Área de Feedback simulada.")
