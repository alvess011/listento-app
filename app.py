import streamlit as st
import google.generativeai as genai
import tempfile
import os
import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Listento Mobile",
    page_icon="🎧",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS (Visual Limpo) ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%; border-radius: 12px; height: 55px; font-weight: bold; font-size: 18px;
        background-color: #FF4B4B; color: white;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: #262730; border: 2px solid #4c4f56;
        color: #ffffff; border-radius: 10px; padding: 10px; flex: 1;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF4B4B !important; color: white !important; border: 2px solid #FF4B4B !important;
    }
    .tutorial-step {
        background-color: #1E1E1E; padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid #FF4B4B;
    }
    .google-btn {
        background-color: #4285F4; color: white !important; text-decoration: none; padding: 10px 25px; border-radius: 20px; font-weight: bold; display: inline-block; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE LOGIN INTELIGENTE ---

# 1. Tenta pegar a chave do "Cofre" (Secrets)
try:
    master_key = st.secrets["GEMINI_API_KEY"]
except:
    master_key = None

# 2. Inicializa a sessão
if 'api_key' not in st.session_state:
    # Se tiver chave mestra, usa ela automaticamente!
    if master_key:
        st.session_state.api_key = master_key
        st.session_state.using_master_key = True
    else:
        st.session_state.api_key = ''
        st.session_state.using_master_key = False

# --- Cabeçalho ---
st.title("🎧 Listento")

# ==========================================
# 🛑 TELA DE LOGIN (Só aparece se NÃO tiver chave mestra e NÃO tiver chave do usuário)
# ==========================================
if not st.session_state.api_key:
    st.info("🔒 Configure seu acesso (Ou peça um link de convite ao administrador).")

    # Passo 1
    st.markdown("""
    <div class="tutorial-step">
        <b>1. Acesse o Google</b><br>
        <div style="text-align:center;"><a href="https://aistudio.google.com/app/apikey" target="_blank" class="google-btn">🔗 Gerar Chave (Grátis)</a></div>
    </div>
    """, unsafe_allow_html=True)
    if os.path.exists("print1.png"): st.image("print1.png", use_container_width=True)

    # Passo 2
    st.markdown("""<div class="tutorial-step"><b>2. Crie a Chave</b><br>Clique em <b>"Create API Key"</b> > <b>"Create in new project"</b>.</div>""", unsafe_allow_html=True)
    if os.path.exists("print2.png"): st.image("print2.png", use_container_width=True)

    # Passo 3
    st.markdown("""<div class="tutorial-step"><b>3. Copie o Código</b><br>Copie o código "AIza..." e cole abaixo.</div>""", unsafe_allow_html=True)
    if os.path.exists("print3.png"): st.image("print3.png", use_container_width=True)

    st.markdown("---")
    key_input = st.text_input("Sua API Key:", type="password", placeholder="Cole aqui", label_visibility="collapsed")
    
    if key_input:
        st.session_state.api_key = key_input
        st.session_state.using_master_key = False
        st.rerun()
    st.stop()

# ==========================================
# 📱 APP PRINCIPAL
# ==========================================
api_key = st.session_state.api_key

# Aviso discreto se estiver usando a chave mestra
if st.session_state.get('using_master_key'):
    st.toast("✅ Acesso Premium Ativado (Chave do Sócio)", icon="🚀")

# ... (RESTO DO CÓDIGO IGUAL - COPIE AS ABAS ABAIXO) ...

tab_audio, tab_text, tab_reply, tab_feedback = st.tabs(["👂 Ouvir", "📖 Ler", "✍️ Responder", "📢 Feedback"])

# --- ABA 1: OUVIR ---
with tab_audio:
    col_lang, col_vazio = st.columns([2, 1])
    with col_lang:
        target_lang = st.selectbox("Traduzir áudio para:", ["Português (Brasil)", "Inglês", "Espanhol", "Francês", "Italiano", "Alemão"])
    
    st.markdown("---")
    uploaded_file = st.file_uploader("Escolher arquivo", type=['mp3', 'wav', 'ogg', 'm4a', 'wma', 'aac', 'flac', 'opus', 'mp4', 'mpeg', 'webm', 'mov'])
    
    if uploaded_file:
        if uploaded_file.type.startswith('video'): st.video(uploaded_file)
        else: st.audio(uploaded_file)
        
        if st.button("Transcrever e Traduzir", key="btn_audio"):
            with st.spinner('Processando...'):
                try:
                    genai.configure(api_key=api_key)
                    file_extension = os.path.splitext(uploaded_file.name)[1]
                    if not file_extension: file_extension = ".mp3"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    audio_file = genai.upload_file(path=tmp_path)
                    
                    prompt = f"""
                    Tarefa: Transcrever e traduzir.
                    1. Transcreva o original.
                    2. Traduza para: {target_lang}.
                    3. Notas de contexto.
                    Formato:
                    ### 📝 Transcrição Original
                    (Texto)
                    ### 🌍 Tradução ({target_lang})
                    (Texto traduzido)
                    ### 💡 Notas de Contexto
                    (Notas)
                    """
                    model = genai.GenerativeModel('gemini-2.0-flash') 
                    response = model.generate_content([prompt, audio_file])
                    st.success("Sucesso!")
                    st.markdown(response.text)
                    os.unlink(tmp_path)
                except Exception as e:
                    st.error(f"Erro: {e}")

# --- ABA 2: LER ---
with tab_text:
    target_lang_text = st.selectbox("Traduzir texto para:", ["Português (Brasil)", "Inglês", "Espanhol"], key="lang_text")
    st.markdown("---")
    client_text = st.text_area("Texto do cliente:", height=150)
    if st.button("Traduzir Texto", key="btn_text"):
        if not client_text: st.warning("Cole texto primeiro.")
        else:
            with st.spinner('Traduzindo...'):
                try:
                    genai.configure(api_key=api_key)
                    prompt = f"""
                    Traduza para {target_lang_text}: "{client_text}".
                    Formato:
                    ### 📄 Original
                    {client_text}
                    ### 🌍 Tradução
                    (Tradução)
                    ### 💡 Notas
                    (Contexto)
                    """
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                except Exception as e: st.error(f"Erro: {e}")

# --- ABA 3: RESPONDER ---
with tab_reply:
    col1, col2 = st.columns(2)
    target_lang_reply = col1.selectbox("Traduzir resposta para:", ["Inglês", "Espanhol", "Francês", "Alemão", "Italiano", "Chinês"])
    tone_reply = col2.selectbox("Tom:", ["Profissional", "Amigável", "Direto"])
    my_reply = st.text_area("Escreva em Português:", height=150)
    
    if st.button("✨ Gerar Resposta", key="btn_reply"):
        if not my_reply: st.warning("Escreva algo.")
        else:
            with st.spinner('Gerando...'):
                try:
                    genai.configure(api_key=api_key)
                    prompt = f"Traduza '{my_reply}' para {target_lang_reply}. Tom: {tone_reply}. Saída: Apenas texto final."
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    response = model.generate_content(prompt)
                    st.success("Copie abaixo:")
                    st.code(response.text, language=None)
                except Exception as e: st.error(f"Erro: {e}")

# --- ABA 4: FEEDBACK ---
with tab_feedback:
    st.markdown("### 📢 Ajude o Listento a evoluir")
    feedback_type = st.selectbox("Tipo:", ["Sugestão", "Erro/Bug", "Elogio"])
    feedback_msg = st.text_area("Sua mensagem:", height=150)
    if st.button("Enviar Feedback", key="btn_feedback"):
        if feedback_msg:
            print(f"FEEDBACK: {feedback_type} - {feedback_msg}")
            st.success("Enviado! Obrigado.")
        else: st.warning("Escreva algo.")
