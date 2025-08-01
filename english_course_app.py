import streamlit as st
import requests
import random
import sqlite3
import tempfile
import os
import datetime
from gtts import gTTS

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
        # Step 1: Get a random word from internet
        word_resp = requests.get("https://random-word-api.herokuapp.com/word?number=1")
        if word_resp.status_code != 200:
            st.warning("Failed to fetch a random word.")
            return None
        word = word_resp.json()[0]

        # Step 2: Use dictionary API to get meaning
        dict_resp = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
        if dict_resp.status_code != 200:
            return None  # Skip if word not found in dictionary
        data = dict_resp.json()[0]

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
        tts.save(fp.name)
        temp_path = fp.name

    with open(temp_path, "rb") as f:
        audio_bytes = f.read()

    os.remove(temp_path)
    return audio_bytes

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

    # Use st.audio for reliable playback
    audio_bytes = tts_audio(word)
    st.audio(audio_bytes, format="audio/mp3")

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
            new_streak = streak  # you could increment if needed
        update_progress(new_streak)
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
