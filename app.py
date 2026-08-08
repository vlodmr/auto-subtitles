import streamlit as st
import whisper
import os
import subprocess

st.set_page_config(page_title="AutoSub Studio", layout="centered")

st.title("🎬 Автоматичні субтитри")
st.write("Завантажте відео та налаштуйте вигляд субтитрів!")

# 1. Завантаження відео
uploaded_file = st.file_uploader("Оберіть відеофайл (MP4, MOV)", type=["mp4", "mov"])

# --- ПАНЕЛЬ НАЛАШТУВАНЬ ВИГЛЯДУ ---
st.subheader("⚙️ Налаштування субтитрів")

col1, col2 = st.columns(2)

with col1:
    style_option = st.selectbox(
        "Стиль субтитрів:",
        [
            "1. TikTok (Жовтий з чорним фоном)",
            "2. Класика (Білий з чорним контуром)",
            "3. Неон (Яскраво-зелений)"
        ]
    )
    font_size = st.slider("🔍 Розмір шрифту (Zoom):", min_value=20, max_value=90, value=50, step=2)

with col2:
    y_position = st.slider("↕️ Положення по вертикалі (% від верху):", min_value=10, max_value=95, value=80, step=5)

# Функція конвертації часу для формату ASS
def format_ass_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    centisecs = int((secs - int(secs)) * 100)
    return f"{hours}:{minutes:02d}:{int(secs):02d}.{centisecs:02d}"

# Функція для генерації файлу субтитрів (.ass)
def generate_ass_file(subtitles_data, ass_path, font_size, y_position, style_option):
    # Визначаємо кольори та стиль (Формат кольорів ASS: &HAlphaBlueGreenRed)
    if "1." in style_option:
        primary_color = "&H0000FFFF"  # Жовтий
        outline_color = "&H00000000"  # Чорний
        back_color = "&H00000000"     # Непрозорий чорний фон
        border_style = 3              # Прямокутник навколо тексту
        outline = 2
    elif "2." in style_option:
        primary_color = "&H00FFFFFF"  # Білий
        outline_color = "&H00000000"  # Чорний контур
        back_color = "&H80000000"
        border_style = 1              # Контур
        outline = 3
    else:
        primary_color = "&H0000FF00"  # Зелений неон
        outline_color = "&H00000000"  # Чорний контур
        back_color = "&H80000000"
        border_style = 1
        outline = 3

    # Розрахунок відступу знизу (MarginV)
    margin_v = int((100 - y_position) * 10.8)

    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{font_size},{primary_color},&H00000000,{outline_color},{back_color},-1,0,0,0,100,100,0,0,{border_style},{outline},0,2,10,10,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        for (start, end), text in subtitles_data:
            start_str = format_ass_time(start)
            end_str = format_ass_time(end)
            f.write(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}\n")

# Розбиття на групи по 3 слова
def group_words(segments, max_words=3):
    grouped = []
    for segment in segments:
        words = segment.get('words', [])
        if not words:
            grouped.append(((segment['start'], segment['end']), segment['text']))
            continue
            
        for i in range(0, len(words), max_words):
            group = words[i:i + max_words]
            start_time = group[0]['start']
            end_time = group[-1]['end']
            text = " ".join([w['word'] for w in group])
            grouped.append(((start_time, end_time), text.strip()))
    return grouped

# --- ОБРОБКА ВІДЕО ---
if uploaded_file is not None:
    with open("temp_input.mp4", "wb") as f:
        f.write(uploaded_file.read())
    
    st.video("temp_input.mp4")
    
    if st.button("🚀 Згенерувати субтитри"):
        with st.spinner("1/2 Розпізнаємо мову (Whisper AI)..."):
            model = whisper.load_model("base")
            result = model.transcribe("temp_input.mp4", language="uk", word_timestamps=True)
            subtitles_data = group_words(result['segments'], max_words=3)

        with st.spinner("2/2 Швидке накладання субтитрів через FFmpeg..."):
            ass_file = "subs.ass"
            output_path = "output_with_subs.mp4"
            
            # Створюємо файл субтитрів
            generate_ass_file(subtitles_data, ass_file, font_size, y_position, style_option)
            
            # Впікаємо субтитри через чистий FFmpeg
            cmd = [
                "ffmpeg", "-y",
                "-i", "temp_input.mp4",
                "-vf", f"subtitles={ass_file}",
                "-c:a", "copy",
                output_path
            ]
            subprocess.run(cmd, check=True)

        st.success("Готово!")
        st.video(output_path)
        
        with open(output_path, "rb") as file:
            st.download_button(
                label="📥 Завантажити готове відео",
                data=file,
                file_name="video_with_subtitles.mp4",
                mime="video/mp4"
            )
