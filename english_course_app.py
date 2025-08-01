import streamlit as st
import random, tempfile, base64, sqlite3, os, datetime, hashlib
from gtts import gTTS

# --------------------
# DATABASE SETUP
# --------------------
def init_db():
    conn = sqlite3.connect("progress.db", check_same_thread=False)
    c = conn.cursor()
    # For simplicity, drop the old tables if exists (only for development)
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS wrong_answers")
    
    c.execute("""
        CREATE TABLE users (
            username TEXT PRIMARY KEY,
            password TEXT,
            xp INTEGER DEFAULT 0,
            last_challenge DATE,
            streak INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE wrong_answers (
            username TEXT,
            question TEXT,
            your_answer TEXT,
            correct_answer TEXT
        )
    """)
    conn.commit()
    return conn

conn = init_db()

# --------------------
# HELPER FUNCTIONS
# --------------------
def hash_pass(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def register_user(username, password):
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO users (username, password, xp, last_challenge, streak) VALUES (?, ?, 0, NULL, 0)",
        (username, hash_pass(password))
    )
    conn.commit()

def login_user(username, password):
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", 
              (username, hash_pass(password)))
    return c.fetchone()

def update_xp(username, delta):
    c = conn.cursor()
    c.execute("UPDATE users SET xp = xp + ? WHERE username = ?", (delta, username))
    conn.commit()

def update_streak(username, today):
    c = conn.cursor()
    c.execute("SELECT last_challenge, streak FROM users WHERE username=?", (username,))
    last, streak = c.fetchone()
    if last != today:
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        if last == yesterday:
            streak += 1
        else:
            streak = 1
        c.execute("UPDATE users SET last_challenge=?, streak=? WHERE username=?", (today, streak, username))
        conn.commit()
        return streak
    return streak

def log_wrong_answer(username, question, your_ans, correct_ans):
    c = conn.cursor()
    c.execute("INSERT INTO wrong_answers (username, question, your_answer, correct_answer) VALUES (?, ?, ?, ?)",
              (username, question, your_ans, correct_ans))
    conn.commit()

def get_leaderboard():
    c = conn.cursor()
    return c.execute("SELECT username, xp FROM users ORDER BY xp DESC LIMIT 5").fetchall()

def get_wrong_answers(username):
    c = conn.cursor()
    return c.execute("SELECT question, your_answer, correct_answer FROM wrong_answers WHERE username=?", (username,)).fetchall()

# --------------------
# VOCAB & GRAMMAR
# --------------------
vocab_data = {
    "en": {
        "apple": "a fruit",
        "run": "to move quickly",
        "book": "a set of pages",
    },
    "es": {
        "manzana": "una fruta",
        "correr": "moverse rápido",
        "libro": "conjunto de páginas"
    }
}

grammar = [
    {"sentence": "She ___ happy.", "options": ["is", "are", "am"], "answer": "is"}
]

def generate_audio(word, lang):
    tts = gTTS(text=word, lang=lang)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        audio_bytes = open(fp.name, "rb").read()
    audio = base64.b64encode(audio_bytes).decode()
    return f"<audio controls><source src='data:audio/mp3;base64,{audio}' type='audio/mp3'></audio>"

# --------------------
# APP SETUP
# --------------------
st.set_page_config(page_title="Language XP App", layout="centered")
st.title("🧠 Language Learning with XP")

# --------------------
# AUTHENTICATION HANDLING
# --------------------

menu = st.sidebar.radio("Navigation", ["Login", "Register", "Leaderboard", "Review Mistakes"])
language = st.sidebar.selectbox("Language", ["en", "es"], format_func=lambda x: "English" if x == "en" else "Español")

if "user" not in st.session_state:
    st.session_state.user = None
if "login_error" not in st.session_state:
    st.session_state.login_error = False

def do_login():
    user = login_user(st.session_state.username, st.session_state.password)
    if user:
        st.session_state.user = st.session_state.username.strip()
        st.session_state.login_error = False
    else:
        st.session_state.login_error = True

if menu == "Register":
    st.subheader("📝 Create Account")
    username = st.text_input("Username", key="reg_username")
    password = st.text_input("Password", type="password", key="reg_password")
    if st.button("Register"):
        if username and password:
            register_user(username.strip(), password)
            st.success("User registered! Go to Login.")
        else:
            st.error("Please enter username and password")

elif menu == "Login":
    st.subheader("🔐 Login")
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password")
    if st.button("Login"):
        do_login()
        if st.session_state.user:
            st.success(f"Logged in as {st.session_state.user}")
            st.experimental_rerun()
        elif st.session_state.login_error:
            st.error("Invalid credentials")
    if st.session_state.user:
        st.info(f"Already logged in as {st.session_state.user}")

elif menu == "Leaderboard":
    st.subheader("🏆 Leaderboard")
    leaderboard = get_leaderboard()
    for u, xp in leaderboard:
        st.write(f"**{u}** — {xp} XP")

elif menu == "Review Mistakes":
    st.subheader("📘 Review Mistakes")
    if not st.session_state.user:
        st.info("Login first.")
    else:
        mistakes = get_wrong_answers(st.session_state.user)
        if mistakes:
            for q, your, correct in mistakes:
                st.markdown(f"**Q:** {q}\n\n*You said:* {your}\n\n✅ Correct: {correct}")
        else:
            st.success("No mistakes logged yet!")

# --------------------
# MAIN LEARNING SECTION
# --------------------
if st.session_state.user and menu in ["Login", ""]:
    today = datetime.date.today().isoformat()
    c = conn.cursor()
    c.execute("SELECT xp, last_challenge, streak FROM users WHERE username=?", (st.session_state.user,))
    xp, last, streak = c.fetchone()

    st.success(f"Welcome, **{st.session_state.user}**! XP: {xp} | Level: {'Beginner' if xp<50 else 'Intermediate' if xp<200 else 'Advanced'}")

    streak = update_streak(st.session_state.user, today)
    st.info(f"🔥 Streak: {streak} days")

    st.markdown("---")
    word = random.choice(list(vocab_data[language].keys()))
    correct_meaning = vocab_data[language][word]
    st.subheader("📖 Vocabulary")
    st.markdown(generate_audio(word, language), unsafe_allow_html=True)
    options = random.sample(list(vocab_data[language].values()), k=len(vocab_data[language]))
    choice = st.selectbox(f"What does **{word}** mean?", options)
    if st.button("Submit Vocabulary"):
        if choice == correct_meaning:
            st.success("Correct! +5 XP")
            update_xp(st.session_state.user, 5)
        else:
            st.error(f"Wrong. Correct: {correct_meaning}")
            log_wrong_answer(st.session_state.user, f"What does '{word}' mean?", choice, correct_meaning)

    st.markdown("---")
    st.subheader("📝 Grammar")
    gq = grammar[0]
    st.write(gq["sentence"])
    g_choice = st.selectbox("Choose the correct word:", gq["options"])
    if st.button("Submit Grammar"):
        if g_choice == gq["answer"]:
            st.success("Correct! +5 XP")
            update_xp(st.session_state.user, 5)
        else:
            st.error(f"Wrong. Correct: {gq['answer']}")
            log_wrong_answer(st.session_state.user, gq["sentence"], g_choice, gq["answer"])
