import streamlit as st
import google.generativeai as genai
import tempfile
import os
import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Listento",
    page_icon="🎧",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS INTELIGENTE (RESPONSIVO) ---
st.markdown("""
    <style>
    /* =========================================
       1. LIMPEZA GERAL (REMOVE MARCAS D'ÁGUA)
       ========================================= */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* =========================================
       2. OTIMIZAÇÃO DE ESPAÇO (PADDING)
       ========================================= */
    /* Diminui o espaço gigante no topo da tela */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 800px; /* No Desktop não fica esticado demais */
    }

    /* =========================================
       3. COMPONENTES VISUAIS
       ========================================= */
    /* Botões Grandes e Clicáveis */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 55px;
        font-weight: bold;
        font-size: 18px;
        background-color: #FF4B4B;
        color: white;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        transition: transform 0.1s;
    }
    .stButton>button:active {
        transform: scale(0.98); /* Efeito de clique */
    }
    
    /* Abas Estilizadas */
    .stTabs [data-baseweb="tab-list"] { 
        gap: 8px; 
        background-color: transparent;
        padding-bottom: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #262730;
        border: 1px solid #
