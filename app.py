import streamlit as st
import whisper
import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip

st.set_page_config(page_title="AutoSub Studio", layout="centered")

st.title("🎬 Автоматичні субтитри")
st.write("Завантажте відео та налаштуйте вигляд субтитрів під себе!")

# 1. Завантаження відео
uploaded_file = st.file_uploader("Оберіть відеофайл (MP4, MOV)", type=["mp4", "mov"])

# --- ПАНЕЛЬ НАЛАШТУВАНЬ ВИГЛЯДУ ---
st.subheader("⚙️ Налаштування субтитрів")

col1, col2 = st.columns(2)

with col1:
    # Вибір стилю
    style_option = st.selectbox(
        "Стиль субтитрів:",
        [
            "1. TikTok (Жовтий з фоном)",
            "2. Класика (Білий з тінню)",
            "3. Неон (Яскраво-зелений)"
        ]
    )
    
    # Zoom In / Zoom Out (Розмір шрифту)
    font_size = st.slider("🔍 Розмір шрифту (Zoom):", min_value=16, max_value=80, value=36, step=2)

with col2:
    # Положення по вертикалі (Y)
    y_position = st.slider("↕️ Положення по вертикалі (% від верху):", min_value=10, max_value=90, value=75, step=5)
    
    # Положення по горизонталі (X)
    x_align = st.selectbox("↔️ Вирівнювання по горизонталі:", ["center", "left", "right"])

# Функція для розбиття тексту по 3 слова
def group_words(segments, max_words=3):
    grouped_subtitles = []
    for segment in segments:
        words = segment.get('words', [])
        if not words:
            grouped_subtitles.append(((segment['start'], segment['end']), segment['text']))
            continue
            
        for i in range(0, len(words), max_words):
            group = words[i:i + max_words]
            start_time = group[0]['start']
            end_time = group[-1]['end']
            text = " ".join([w['word'] for w in group])
            grouped_subtitles.append(((start_time, end_time), text.strip()))
    return grouped_subtitles

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

        with st.spinner("2/2 Накладаємо субтитри та рендеримо..."):
            video = VideoFileClip("temp_input.mp4")
            
            # Налаштування кольорів залежно від стилю
            is_style_1 = "1." in style_option
            is_style_2 = "2." in style_option
            
            generator = lambda txt: TextClip(
                txt,
                font='Arial-Bold',
                fontsize=font_size,  # Використовуємо розмір зі слайдера
                color='yellow' if is_style_1 else ('white' if is_style_2 else '#00FF66'),
                bg_color='black' if is_style_1 else None,
                stroke_color='black' if (is_style_2 or not is_style_1) else None,
                stroke_width=2 if (is_style_2 or not is_style_1) else 0,
                method='caption',
                size=(int(video.w * 0.85), None)
            )

            subtitles = SubtitlesClip(subtitles_data, generator)
            
            # Динамічне розрахування позиції (Y-вертикаль, X-горизонталь)
            pos_y = video.h * (y_position / 100.0)
            subtitles = subtitles.set_position((x_align, pos_y))
            
            final_video = CompositeVideoClip([video, subtitles])
            output_path = "output_with_subs.mp4"
            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")

        st.success("Готово!")
        st.video(output_path)
        
        with open(output_path, "rb") as file:
            st.download_button(
                label="📥 Завантажити готове відео",
                data=file,
                file_name="video_with_subtitles.mp4",
                mime="video/mp4"
            )
