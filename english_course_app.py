import streamlit as st
import random, tempfile, base64, sqlite3, os, datetime
from gtts import gTTS

# --------------------
# DB SETUP
# --------------------
def init_db():
    conn = sqlite3.connect("progress.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY,
            xp INTEGER,
            streak INTEGER,
            last_date TEXT,
            level TEXT
        )
    """)
    # Ensure one user row
    c.execute("SELECT COUNT(*) FROM user_progress")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO user_progress (xp, streak, last_date, level) VALUES (0,0,'', 'beginner')")
    conn.commit()
    return conn

conn = init_db()

# --------------------
# LESSON DATA
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
def get_user_progress():
    c = conn.cursor()
    c.execute("SELECT xp, streak, last_date, level FROM user_progress WHERE id=1")
    return c.fetchone()

def update_user_progress(xp=None, streak=None, last_date=None, level=None):
    c = conn.cursor()
    current = get_user_progress()
    new_xp = xp if xp is not None else current[0]
    new_streak = streak if streak is not None else current[1]
    new_date = last_date if last_date is not None else current[2]
    new_level = level if level is not None else current[3]
    c.execute("""UPDATE user_progress SET xp=?, streak=?, last_date=?, level=? WHERE id=1""",
              (new_xp, new_streak, new_date, new_level))
    conn.commit()

def generate_audio(word, lang="en"):
    tts = gTTS(text=word, lang=lang)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        audio_bytes = open(fp.name, "rb").read()
    audio = base64.b64encode(audio_bytes).decode()
    os.unlink(fp.name)
    return f"<audio controls><source src='data:audio/mp3;base64,{audio}' type='audio/mp3'></audio>"

def get_level_by_xp(xp):
    if xp < 20:
        return "beginner"
    elif xp < 50:
        return "intermediate"
    else:
        return "advanced"

# --------------------
# APP LOGIC
# --------------------
st.set_page_config(page_title="Daily Language Lesson", layout="centered")
st.title("🌟 Daily Language Lesson (Duolingo Style)")

# Load progress
xp, streak, last_date, level = get_user_progress()

# Update streak if last_date is yesterday
today = datetime.date.today().isoformat()
yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
if last_date != today:
    if last_date == yesterday:
        streak += 1
    else:
        streak = 1
    update_user_progress(streak=streak, last_date=today)

# Update level if XP changed
new_level = get_level_by_xp(xp)
if new_level != level:
    level = new_level
    update_user_progress(level=level)

st.write(f"**Level:** {level.capitalize()} | **XP:** {xp} | **Streak:** {streak} days 🔥")

# Initialize session state for question type and current item index
if "question_type" not in st.session_state:
    st.session_state.question_type = "vocab"  # vocab or grammar
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
if "answered" not in st.session_state:
    st.session_state.answered = False
if "current_word" not in st.session_state:
    st.session_state.current_word = None
if "current_correct" not in st.session_state:
    st.session_state.current_correct = None
if "current_options" not in st.session_state:
    st.session_state.current_options = []

lesson_data = lessons[level]

def load_new_vocab_question():
    word = random.choice(list(lesson_data["vocab"].keys()))
    correct = lesson_data["vocab"][word]
    options = list(lesson_data["vocab"].values())
    random.shuffle(options)
    st.session_state.current_word = word
    st.session_state.current_correct = correct
    st.session_state.current_options = options
    st.session_state.question_type = "vocab"
    st.session_state.answered = False

def load_new_grammar_question():
    q = random.choice(lesson_data["grammar"])
    st.session_state.current_word = q["sentence"]
    st.session_state.current_correct = q["answer"]
    st.session_state.current_options = q["options"]
    st.session_state.question_type = "grammar"
    st.session_state.answered = False

# Load initial question if none
if st.session_state.current_word is None:
    load_new_vocab_question()

st.subheader("Your Lesson")

if st.session_state.question_type == "vocab":
    st.markdown(generate_audio(st.session_state.current_word), unsafe_allow_html=True)
    st.write(f"What does **{st.session_state.current_word}** mean?")
else:
    st.write(st.session_state.current_word)

choice = st.selectbox("Choose your answer:", st.session_state.current_options, key="answer_select")

if st.session_state.answered:
    if choice == st.session_state.current_correct:
        st.success("Correct! +5 XP")
    else:
        st.error(f"Wrong. Correct answer: {st.session_state.current_correct}")

if st.button("Submit") and not st.session_state.answered:
    if choice == st.session_state.current_correct:
        xp += 5
        update_user_progress(xp=xp)
    st.session_state.answered = True

if st.session_state.answered:
    if st.button("Next Question"):
        if st.session_state.question_type == "vocab":
            load_new_grammar_question()
        else:
            load_new_vocab_question()
        st.rerun()
        # Stop further code execution after rerun to avoid error:
        st.stop()

st.markdown("---")
st.write("Keep practicing every day to build your streak and level up!")

