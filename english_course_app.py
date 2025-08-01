import streamlit as st
import random, tempfile, base64, sqlite3
from gtts import gTTS
import os
import datetime

# Optional: for offline speech‑to‑text
try:
    import whisper
except:
    whisper = None

def init_db():
    conn = sqlite3.connect("progress.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        xp INTEGER DEFAULT 0,
        last_challenge DATE
    )""")
    conn.commit()
    return conn

conn = init_db()

def register_user(name):
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username,xp,last_challenge) VALUES (?,?,?)",
              (name, 0, ""))
    conn.commit()

def update_xp(name, delta):
    c = conn.cursor()
    c.execute("UPDATE users SET xp = xp + ? WHERE username = ?", (delta, name))
    conn.commit()

def fetch_user(name):
    c = conn.cursor()
    c.execute("SELECT xp,last_challenge FROM users WHERE username=?", (name,))
    return c.fetchone()

vocab = {"apple": "a fruit", "run": "to move quickly", "book": "a set of pages"}
grammar = [{"sentence":"She ___ happy.", "options":["is","are","am"], "answer":"is"}]

def generate_audio(word):
    tts = gTTS(text=word, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        audio_bytes = open(fp.name, "rb").read()
    audio = base64.b64encode(audio_bytes).decode()
    return f"<audio controls><source src='data:audio/mp3;base64,{audio}' type='audio/mp3'></audio>"

def transcribe_audio(wav_bytes):
    if whisper:
        model = whisper.load_model("base")
        result = model.transcribe(wav_bytes)
        return result["text"].strip()
    else:
        import speech_recognition as sr
        rec = sr.Recognizer()
        audio = sr.AudioFile(wav_bytes)
        with audio as source:
            rec.adjust_for_ambient_noise(source)
            audio_data = rec.record(source)
        return rec.recognize_google(audio_data)

# UI
st.title("🧠 English Course with XP & Voice Scoring")
user = st.text_input("Enter your name to begin")
if user:
    register_user(user)
    xp,last = fetch_user(user)
    st.write(f"XP: **{xp}**")

    level = "Beginner" if xp<50 else "Intermediate" if xp<200 else "Advanced"
    st.write(f"Level: **{level}**")

    today = datetime.date.today().isoformat()
    if last != today:
        st.write("🎯 Today's challenge: Pronounce 'apple'")
        if st.button("Complete"):
            update_xp(user,10)
            conn.execute("UPDATE users SET last_challenge=? WHERE username=?",(today,user))
            conn.commit()
            st.success("Challenge complete +10 XP!")
    st.markdown("---")

    word = random.choice(list(vocab.keys()))
    st.subheader("Vocabulary Section")
    st.markdown(generate_audio(word), unsafe_allow_html=True)
    choice = st.selectbox("Meaning:", list(vocab.values()))
    if st.button("Submit Vocab"):
        if choice == vocab[word]:
            st.success("Correct! +5 XP")
            update_xp(user,5)
        else:
            st.error(f"Wrong, answer: {vocab[word]}")
    st.markdown("---")

    st.subheader("Pronunciation Practice")
    st.write(f"Pronounce the word **{word}** and upload your recording (.wav, .mp3)")
    f = st.file_uploader("Upload audio recording", type=["wav","mp3"])
    if f:
        st.audio(f)
        try:
            text = transcribe_audio(f)
            st.write("You said:",text)
            score = 100 if text.lower() == word.lower() else max(0, 100 - 50)
            st.write(f"Pronunciation score: **{score}/100**")
            if score > 80:
                update_xp(user,score//10)
                st.success(f"+{score//10} XP earned")
        except Exception as e:
            st.error("Could not transcribe audio")

    st.markdown("---")
    st.subheader("Grammar Section")
    q = grammar[0]
    st.write(q["sentence"])
    g = st.selectbox("Answer:", q["options"])
    if st.button("Submit Grammar"):
        if g == q["answer"]:
            st.success("Correct! +5 XP")
            update_xp(user,5)
        else:
            st.error(f"Wrong, correct is {q['answer']}")
    st.markdown("---")

    xp_after,last = fetch_user(user)
    st.write(f"Total XP: **{xp_after}**")
    st.write(f"Current Level: **{'Beginner' if xp_after<50 else 'Intermediate' if xp_after<200 else 'Advanced'}**")
