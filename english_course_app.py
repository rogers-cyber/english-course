import streamlit as st
import random, tempfile, base64, sqlite3, os, datetime
from gtts import gTTS

# --------------------
# DATABASE SETUP
# --------------------
def init_db():
    conn = sqlite3.connect("progress.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            date TEXT PRIMARY KEY,
            xp INTEGER,
            streak INTEGER
        )
    """)
    conn.commit()
    return conn

conn = init_db()

# --------------------
# VOCAB & GRAMMAR DATA (example sets for 3 levels)
# --------------------
lessons = {
    "beginner": {
        "vocab": {
            "apple": "a fruit",
            "run": "to move quickly",
            "book": "a set of pages",
        },
        "grammar": [
            {"sentence": "She ___ happy.", "options": ["is", "are", "am"], "answer": "is"}
        ]
    },
    "intermediate": {
        "vocab": {
            "challenge": "a difficult task",
            "improve": "to get better",
            "travel": "to go from one place to another",
        },
        "grammar": [
            {"sentence": "They ___ going to the park.", "options": ["is", "are", "am"], "answer": "are"}
        ]
    },
    "advanced": {
        "vocab": {
            "meticulous": "showing great attention to detail",
            "ubiquitous": "present everywhere",
            "candid": "truthful and straightforward",
        },
        "grammar": [
            {"sentence": "Had I ___ known, I would have come.", "options": ["have", "has", "had"], "answer": "had"}
        ]
    }
}

# --------------------
# UTILS
# --------------------
def generate_audio(word, lang="en"):
    tts = gTTS(text=word, lang=lang)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        audio_bytes = open(fp.name, "rb").read()
    audio = base64.b64encode(audio_bytes).decode()
    os.unlink(fp.name)
    return f"<audio controls><source src='data:audio/mp3;base64,{audio}' type='audio/mp3'></audio>"

def get_progress():
    c = conn.cursor()
    today = datetime.date.today().isoformat()
    c.execute("SELECT xp, streak FROM progress WHERE date=?", (today,))
    row = c.fetchone()
    if row:
        return row
    else:
        return 0, 0

def update_progress(xp_delta, new_streak):
    c = conn.cursor()
    today = datetime.date.today().isoformat()
    xp, streak = get_progress()
    xp += xp_delta
    streak = new_streak
    c.execute("INSERT OR REPLACE INTO progress (date, xp, streak) VALUES (?, ?, ?)", (today, xp, streak))
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

def get_level(xp):
    if xp < 20:
        return "beginner"
    elif xp < 50:
        return "intermediate"
    else:
        return "advanced"

# --------------------
# APP START
# --------------------
st.set_page_config(page_title="Daily Language Lesson", layout="centered")
st.title("🌟 Daily Language Lesson")

# Load progress
xp, streak = get_progress()
streak = get_streak()
level = get_level(xp)

st.info(f"Your current level is **{level.capitalize()}** with **{xp} XP** and a **{streak}-day streak** 🔥")

# Select today's lesson based on level
lesson = lessons[level]

# Vocabulary quiz
st.subheader("📖 Vocabulary")
word = random.choice(list(lesson["vocab"].keys()))
correct_meaning = lesson["vocab"][word]
st.markdown(generate_audio(word), unsafe_allow_html=True)

options = list(lesson["vocab"].values())
random.shuffle(options)
choice = st.selectbox(f"What does **{word}** mean?", options)

if st.button("Submit Vocabulary"):
    if choice == correct_meaning:
        st.success("Correct! +5 XP")
        update_progress(5, streak)
    else:
        st.error(f"Wrong. Correct answer: {correct_meaning}")

# Grammar quiz
st.markdown("---")
st.subheader("📝 Grammar")
gq = random.choice(lesson["grammar"])
st.write(gq["sentence"])
g_choice = st.selectbox("Choose the correct word:", gq["options"])

if st.button("Submit Grammar"):
    if g_choice == gq["answer"]:
        st.success("Correct! +5 XP")
        update_progress(5, streak)
    else:
        st.error(f"Wrong. Correct answer: {gq['answer']}")

# Show XP and streak at bottom
st.markdown("---")
st.write(f"**XP:** {xp} | **Streak:** {streak} days | **Level:** {level.capitalize()}")

