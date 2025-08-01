import streamlit as st
import requests
import random
import sqlite3
import tempfile
import base64
import os
import datetime
from gtts import gTTS
import uuid

# -------- DATABASE SETUP --------
def init_db():
    conn = sqlite3.connect("progress.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            date TEXT PRIMARY KEY,
            streak INTEGER
        )
    """)
    conn.commit()
    return conn

conn = init_db()

# -------- VOCAB FETCH FROM API --------
def fetch_random_word_data():
    try:
        word_list = ["apple", "run", "book", "happy", "dog", "challenge", "improve", "travel", "advice", "weather",
                     "meticulous", "ubiquitous", "candid", "benevolent", "paradox"]
        word = random.choice(word_list)
        response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
        if response.status_code != 200:
            return None
        data = response.json()[0]
        meanings = data.get("meanings", [])
        if not meanings:
            return None
        definitions = meanings[0].get("definitions", [])
        if not definitions:
            return None
        meaning = definitions[0].get("definition", "No definition available.")
        example = definitions[0].get("example", "No example provided.")
        return {"word": word, "meaning": meaning, "example": example}
    except Exception as e:
        st.error(f"Error fetching word: {e}")
        return None

# -------- AUDIO UTILITY --------
def tts_audio(text, lang="en"):
    tts = gTTS(text=text, lang=lang)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        temp_path = fp.name
        tts.save(temp_path)

    with open(temp_path, "rb") as audio_file:
        audio_bytes = audio_file.read()

    os.remove(temp_path)
    audio_b64 = base64.b64encode(audio_bytes).decode()

    # Generate a unique id to append as a query param to force reload
    unique_id = uuid.uuid4()

    audio_html = f"""
    <audio controls autoplay>
        <source src="data:audio/mp3;base64,{audio_b64}?id={unique_id}" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>
    """
    return audio_html

# -------- PROGRESS MANAGEMENT --------
def get_progress():
    c = conn.cursor()
    today = datetime.date.today().isoformat()
    c.execute("SELECT streak FROM progress WHERE date=?", (today,))
    row = c.fetchone()
    return row[0] if row else 0

def update_progress(new_streak):
    today = datetime.date.today().isoformat()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO progress (date, streak) VALUES (?, ?)", (today, new_streak))
    conn.commit()

def get_streak():
    c = conn.cursor()
    today = datetime.date.today()
    yesterday = (today - datetime.timedelta(days=1)).isoformat()
    c.execute("SELECT date, streak FROM progress ORDER BY date DESC LIMIT 1")
    row = c.fetchone()
    if row:
        last_date, last_streak = row
        if last_date == yesterday:
            return last_streak + 1
    return 1

# -------- APP START --------
st.set_page_config(page_title="English Word Practice", layout="centered")
st.title("🌟 English Word Practice")

# Load progress
streak = get_streak()

st.info(f"🔥 Streak: **{streak} days**")

# Initialize current word in session state if not present
if "current_word" not in st.session_state:
    word_data = fetch_random_word_data()
    if word_data:
        st.session_state.current_word = word_data
    else:
        st.error("Could not fetch word. Try again later.")

word_data = st.session_state.get("current_word")

# -------- WORD DISPLAY --------
if word_data:
    word = word_data["word"]
    meaning = word_data["meaning"]
    example = word_data["example"]

    st.subheader("🧠 Vocabulary")
    st.markdown(f"### 🔤 Word: `{word}`")
    # Make sure TTS updates every time by using a key to force Streamlit to reload audio
    st.markdown(tts_audio(word), unsafe_allow_html=True)
    st.markdown(f"**Meaning:** {meaning}")
    st.markdown(f"*Example:* _{example}_")

# Buttons to update progress or get new word
col1, col2 = st.columns(2)

with col1:
    if st.button("✅ I Know This Word (+1 Streak)"):
        new_streak = streak
        if streak == 0:
            new_streak = 1
        else:
            new_streak = streak  # keep current streak, or you can add logic to increase if you want
        update_progress(new_streak)
        # fetch a new word
        new_word = fetch_random_word_data()
        if new_word:
            st.session_state.current_word = new_word
        else:
            st.error("Could not fetch a new word.")
        st.rerun()

with col2:
    if st.button("🔄 New Word (No Streak Change)"):
        new_word = fetch_random_word_data()
        if new_word:
            st.session_state.current_word = new_word
        else:
            st.error("Could not fetch a new word.")
        st.rerun()

# -------- STATS DISPLAY --------
st.markdown("---")
st.write(f"🔥 **Streak:** {streak} days")
