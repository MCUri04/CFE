import streamlit as st
import re
from googleapiclient.discovery import build
import google.generativeai as genai

# --- DISEÑO DE LA PÁGINA ---
st.set_page_config(page_title="Analizador de YouTube", page_icon="📊")
st.title("📊 Analizador de Sentimientos de YouTube")
st.write("Descubre qué opina la gente sobre un video sin tener que leer todos los comentarios.")

# --- MENÚ LATERAL PARA LAS LLAVES (SEGURIDAD) ---
st.sidebar.header("🔑 Configuración")
st.sidebar.write("Pega aquí las llaves que guardaste en tu bloc de notas. Esto es seguro y no se guardarán.")
youtube_api_key = st.sidebar.text_input("Llave de YouTube", type="password")
gemini_api_key = st.sidebar.text_input("Llave de Gemini", type="password")

# --- ENTRADA DEL USUARIO ---
video_url = st.text_input("🔗 Pega el enlace del video de YouTube aquí:")

# --- FUNCIONES DEL SISTEMA ---
def obtener_id_video(url):
    # Recorta el enlace para sacar solo el código único del video
    patron = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    resultado = re.search(patron, url)
    return resultado.group(1) if resultado else None

def extraer_comentarios(video_id, llave_youtube):
    # Se conecta a YouTube y descarga los 50 comentarios principales
    youtube = build('youtube', 'v3', developerKey=llave_youtube)
    respuesta = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=50, 
        textFormat="plainText"
    ).execute()
    
    comentarios = [item["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for item in respuesta.get("items", [])]
    return " ".join(comentarios)

def analizar_con_ia(texto_comentarios, llave_gemini):
    # Conectar con la llave secreta
    genai.configure(api_key=llave_gemini)
    
    # Buscar automáticamente el nombre del motor disponible
    nombre_correcto = None
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            nombre_correcto = m.name
            break
            
    # Usar el motor que encontró
    modelo = genai.GenerativeModel(nombre_correcto)
    
    instruccion = f"""
    Actúa como un experto. Lee estos comentarios de YouTube y crea un reporte con:
    1. Sentimiento general (Positivo, Negativo o Neutral)
    2. Los 3 temas o quejas más repetidos.
    3. Una conclusión breve.
    
    Comentarios: {texto_comentarios}
    """
    respuesta = modelo.generate_content(instruccion)
    return respuesta.text

# --- BOTÓN DE ACCIÓN ---
if st.button("🚀 Analizar Video"):
    if not youtube_api_key or not gemini_api_key:
        st.warning("⚠️ Por favor, pega tus llaves en el menú de la izquierda primero.")
    elif not video_url:
        st.warning("⚠️ Por favor, pega un enlace de YouTube válido.")
    else:
        try:
            with st.spinner("1️⃣ Buscando el video..."):
                video_id = obtener_id_video(video_url)
                
            if not video_id:
                st.error("No se pudo encontrar el video. Revisa el enlace.")
            else:
                with st.spinner("2️⃣ Descargando comentarios de YouTube..."):
                    comentarios = extraer_comentarios(video_id, youtube_api_key)
                    
                with st.spinner("3️⃣ La Inteligencia Artificial está analizando (toma unos segundos)..."):
                    resultado = analizar_con_ia(comentarios, gemini_api_key)
                    
                st.success("¡Análisis completado!")
                st.markdown("### 📝 Resultados del Análisis")
                st.write(resultado)
                
        except Exception as e:
            st.error(f"Ocurrió un error detallado: {e}")
