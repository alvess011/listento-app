import streamlit as st
import google.generativeai as genai
import tempfile
import os
import datetime
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
    [data-testid='stFileUploader'] section { padding: 15px; background-color: #1E1E1E; border: 1px dashed #555; }
    @media (max-width: 640px) {
        h1 { font-size: 1.8rem !important; text-align: center; margin-bottom: 0px; }
        .stTabs [data-baseweb="tab"] { font-size: 12px; padding: 0 5px; }
    }
    .tutorial-step {
        background-color: #1E1E1E; padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid #FF4B4B;
    }
    .google-btn {
        background-color: #4285F4; color: white !important; text-decoration: none; padding: 10px 25px; border-radius: 20px; font-weight: bold; display: inline-block; margin-top: 10px;
    }
    .error-box {
        padding: 15px; border-radius: 8px; background-color: #3d1212; border: 1px solid #ff4b4b; color: #ffcccc; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE LOGIN (COM CHAVE HARDCODED) ---
# Aqui inserimos sua chave diretamente para facilitar os testes
master_key = "AIzaSyCnbSkYAcX3XJrdCk9-tfvUJd0CVgXd2v4"

if 'api_key' not in st.session_state:
    if master_key:
        st.session_state.api_key = master_key
        st.session_state.using_master_key = True
    else:
        st.session_state.api_key = ''
        st.session_state.using_master_key = False

# --- Cabeçalho ---
st.title("🎧 Listento")

# ==========================================
# 🛑 TELA DE LOGIN (Vai ser pulada automaticamente)
# ==========================================
if not st.session_state.api_key:
    st.info("🔒 Configure seu acesso.")
    # (Código da tela de login omitido visualmente pois será pulado)
    st.stop()

# ==========================================
# 📱 APP PRINCIPAL
# ==========================================
api_key = st.session_state.api_key
if st.session_state.get('using_master_key'):
    st.toast("✅ Conectado (Modo Teste)", icon="🚀")

tab_audio, tab_text, tab_reply, tab_feedback = st.tabs(["👂 Ouvir", "📖 Ler", "✍️ Responder", "📢 Feedback"])

# --- ABA 1: OUVIR (COM SUPORTE A ARQUIVOS LONGOS E TRATAMENTO DE ERRO) ---
with tab_audio:
    target_lang = st.selectbox("Traduzir áudio para:", ["Português (Brasil)", "Inglês", "Espanhol", "Francês", "Italiano", "Alemão"])
    st.markdown("<div style='margin-bottom: 10px'></div>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Escolher arquivo", type=['mp3', 'wav', 'ogg', 'm4a', 'wma', 'aac', 'flac', 'opus', 'mp4', 'mpeg', 'webm', 'mov'], label_visibility="collapsed")
    
    if uploaded_file:
        if uploaded_file.type.startswith('video'):
            st.video(uploaded_file)
        else:
            st.audio(uploaded_file)
        
        if st.button("Transcrever e Traduzir", key="btn_audio"):
            try:
                genai.configure(api_key=api_key)
                
                # 1. Salvar arquivo temporário
                file_extension = os.path.splitext(uploaded_file.name)[1]
                if not file_extension: file_extension = ".mp3"
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                # 2. Upload para o servidor do Google
                with st.spinner('📤 Enviando arquivo para o cérebro da IA...'):
                    google_file = genai.upload_file(path=tmp_path)
                
                # 3. Lógica de Espera (Polling)
                with st.spinner('⚙️ Processando áudio/vídeo (isso pode levar alguns segundos)...'):
                    while google_file.state.name == "PROCESSING":
                        time.sleep(2)
                        google_file = genai.get_file(google_file.name)
                    
                    if google_file.state.name == "FAILED":
                        raise ValueError("O processamento do arquivo falhou no Google.")

                # 4. Gerar Conteúdo
                with st.spinner('🧠 Traduzindo e analisando contexto...'):
                    prompt = f"""
                    Atue como um transcritor expert.
                    O arquivo fornecido pode ser um áudio ou vídeo longo.
                    
                    TAREFA:
                    1. Transcreva TUDO o que for falado, do início ao fim.
                    2. Traduza a transcrição completa para: {target_lang}.
                    3. Notas de Contexto: Explique o tom, gírias ou detalhes culturais.
                    
                    FORMATO DE SAÍDA (Markdown):
                    ### 📝 Transcrição Completa
                    (Texto original aqui)
                    
                    ### 🌍 Tradução ({target_lang})
                    (Texto traduzido aqui)
                    
                    ### 💡 Notas de Contexto
                    (Bullet points aqui)
                    """
                    
                    model = genai.GenerativeModel('gemini-2.0-flash') 
                    response = model.generate_content([prompt, google_file])
                    
                    logger.info(f"ARQUIVO PROCESSADO | Nome: {uploaded_file.name} | Tamanho: {uploaded_file.size}")
                    
                    st.success("Processamento Concluído!")
                    st.markdown(response.text)
                
                # Limpeza
                os.unlink(tmp_path)

            except Exception as e:
                error_message = str(e)
                if "429" in error_message or "quota" in error_message.lower():
                    st.markdown("""
                        <div class="error-box">
                            <b>⚠️ Limite da Cota Gratuita Atingido</b><br>
                            O Google pausou suas requisições temporariamente.<br>
                            Tente aguardar 1 minuto ou troque a chave novamente no código.
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"Erro técnico: {e}")
                logger.error(f"ERRO AUDIO: {e}")

# --- ABA 2: LER ---
with tab_text:
    target_lang_text = st.selectbox("Traduzir texto para:", ["Português (Brasil)", "Inglês", "Espanhol"], key="lang_text")
    st.markdown("<div style='margin-bottom: 10px'></div>", unsafe_allow_html=True)
    client_text = st.text_area("Texto do cliente:", height=150, placeholder="Cole o texto aqui", label_visibility="collapsed")
    
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
                except Exception as e: 
                    if "429" in str(e):
                        st.warning("⚠️ Cota excedida. Aguarde um momento.")
                    else:
                        st.error(f"Erro: {e}")

# --- ABA 3: RESPONDER ---
with tab_reply:
    col1, col2 = st.columns(2)
    target_lang_reply = col1.selectbox("Traduzir para:", ["Inglês", "Espanhol", "Francês", "Alemão", "Italiano", "Chinês"])
    tone_reply = col2.selectbox("Tom:", ["Profissional", "Amigável", "Direto"])
    my_reply = st.text_area("Escreva em Português:", height=150, placeholder="Sua resposta...", label_visibility="collapsed")
    
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
                except Exception as e: 
                     if "429" in str(e):
                        st.warning("⚠️ Cota excedida. Aguarde um momento.")
                     else:
                        st.error(f"Erro: {e}")

# --- ABA 4: FEEDBACK ---
with tab_feedback:
    st.markdown("### 📢 Ajude o Listento a evoluir")
    with st.form(key='feedback_form', clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1: feedback_type = st.selectbox("Tipo:", ["Sugestão", "Erro/Bug", "Elogio"])
        with col2: feedback_email = st.text_input("Seu E-mail (Opcional):", placeholder="Para novidades...")
        feedback_msg = st.text_area("Sua mensagem:", height=150, placeholder="Escreva aqui...")
        submit_button = st.form_submit_button(label="Enviar Feedback")
        if submit_button:
            if feedback_msg:
                email_info = f"E-MAIL: {feedback_email}" if feedback_email else "E-MAIL: Anônimo"
                logger.info(f"NOVO FEEDBACK | TIPO: {feedback_type} | {email_info} | MSG: {feedback_msg}")
                st.success("Enviado! Obrigado.")
                st.balloons()
            else:
                st.warning("Escreva algo.")
