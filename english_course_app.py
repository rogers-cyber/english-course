import streamlit as st
import random, tempfile, base64, sqlite3, os, datetime
from gtts import gTTS

# ----------- DATABASE SETUP -----------

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

# ----------- DATA SETUP -----------

# Vocabulary now includes sentence examples too
lessons = {
    "beginner": {
        "vocab": {
            "apple": {
                "meaning": "a fruit",
                "example": "I ate a red apple for breakfast."
            },
            "run": {
                "meaning": "to move quickly",
                "example": "She can run very fast."
            },
            "book": {
                "meaning": "a set of pages",
                "example": "This book is about history."
            },
            "happy": {
                "meaning": "feeling joy",
                "example": "He feels happy today."
            },
            "dog": {
                "meaning": "a common pet animal",
                "example": "The dog barked loudly."
            },
        },
        "grammar": [
            {"sentence": "She ___ happy.", "options": ["is", "are", "am"], "answer": "is"},
            {"sentence": "They ___ dogs.", "options": ["have", "has", "haves"], "answer": "have"},
        ],
    },
    "intermediate": {
        "vocab": {
            "challenge": {
                "meaning": "a difficult task",
                "example": "This math problem is a big challenge."
            },
            "improve": {
                "meaning": "to get better",
                "example": "Practice helps you improve your skills."
            },
            "travel": {
                "meaning": "to go from one place to another",
                "example": "We like to travel during holidays."
            },
            "advice": {
                "meaning": "a suggestion",
                "example": "My teacher gave me good advice."
            },
            "weather": {
                "meaning": "the state of the air outside",
                "example": "The weather is sunny today."
            },
        },
        "grammar": [
            {"sentence": "They ___ going to the park.", "options": ["is", "are", "am"], "answer": "are"},
            {"sentence": "I ___ never seen that movie.", "options": ["have", "has", "had"], "answer": "have"},
        ],
    },
    "advanced": {
        "vocab": {
            "meticulous": {
                "meaning": "showing great attention to detail",
                "example": "She is meticulous when organizing her desk."
            },
            "ubiquitous": {
                "meaning": "present everywhere",
                "example": "Smartphones are ubiquitous these days."
            },
            "candid": {
                "meaning": "truthful and straightforward",
                "example": "He gave a candid answer to the question."
            },
            "benevolent": {
                "meaning": "kind and generous",
                "example": "The benevolent leader helped the community."
            },
            "paradox": {
                "meaning": "a seemingly contradictory statement",
                "example": "The statement 'less is more' is a paradox."
            },
        },
        "grammar": [
            {"sentence": "Had I ___ known, I would have come.", "options": ["have", "has", "had"], "answer": "had"},
            {"sentence": "No sooner ___ she arrive than it started raining.", "options": ["did", "do", "does"], "answer": "did"},
        ],
    },
}

# Hints remain simple for easier understanding
hints = {
    "apple": "A common fruit, often red or green.",
    "run": "To move fast on foot.",
    "book": "Pages bound together to read.",
    "happy": "Feeling joy or pleasure.",
    "dog": "A common pet animal.",
    "challenge": "Something difficult to do.",
    "improve": "To get better at something.",
    "travel": "To go to different places.",
    "advice": "A helpful suggestion.",
    "weather": "The state of the air outside.",
    "meticulous": "Very careful and precise.",
    "ubiquitous": "Found everywhere or very common.",
    "candid": "Honest and straightforward.",
    "benevolent": "Kind and generous.",
    "paradox": "A statement that seems contradictory.",
}

# ----------- UTILS -----------

def generate_audio(word, lang="en"):
    tts = gTTS(text=word, lang=lang)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        audio_bytes = open(fp.name, "rb").read()
    os.unlink(fp.name)
    audio_b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
    <audio controls autoplay>
        <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
    </audio>
    """
    return audio_html

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

# ----------- APP START -----------

st.set_page_config(page_title="English Learning Journey", layout="centered")
st.title("🌟 English Learning Journey")

# Load user progress
xp, _ = get_progress()
streak = get_streak()
level = get_level(xp)

st.info(f"Your current level is **{level.capitalize()}** with **{xp} XP** and a **{streak}-day streak** 🔥")

lesson = lessons[level]

# Initialize vocab session state on first run
if "vocab_word" not in st.session_state:
    st.session_state.vocab_word = random.choice(list(lesson["vocab"].keys()))
    vocab_options = [lesson["vocab"][w]["meaning"] for w in lesson["vocab"]]
    random.shuffle(vocab_options)
    st.session_state.vocab_options = vocab_options

# -------- Vocabulary Quiz --------
with st.form("vocab_form"):
    word = st.session_state.vocab_word
    correct_meaning = lesson["vocab"][word]["meaning"]
    example_sentence = lesson["vocab"][word]["example"]

    st.subheader("📖 Vocabulary")
    st.markdown(f"**Your word:** {word}")
    st.markdown(f"*Hint:* {hints.get(word, correct_meaning)}")
    st.markdown(f"**Example:** {example_sentence}")
    st.markdown(generate_audio(word), unsafe_allow_html=True)

    choice = st.selectbox(f"Choose the correct meaning of **{word}**:", st.session_state.vocab_options, key="vocab_choice")

    submitted_vocab = st.form_submit_button("Submit Vocabulary")

    if submitted_vocab:
        if choice == correct_meaning:
            st.success("Correct! +5 XP")
            update_progress(5, streak)
        else:
            st.error(f"Wrong. The correct answer is: {correct_meaning}")

        # Pick a new vocab word and shuffle options for next round
        st.session_state.vocab_word = random.choice(list(lesson["vocab"].keys()))
        vocab_options = [lesson["vocab"][w]["meaning"] for w in lesson["vocab"]]
        random.shuffle(vocab_options)
        st.session_state.vocab_options = vocab_options

# -------- Grammar Quiz --------
with st.form("grammar_form"):
    gq = random.choice(lesson["grammar"])
    st.subheader("📝 Grammar")
    st.write(gq["sentence"])
    g_choice = st.selectbox("Choose the correct word:", gq["options"], key="grammar_choice")

    submitted_grammar = st.form_submit_button("Submit Grammar")

    if submitted_grammar:
        if g_choice == gq["answer"]:
            st.success("Correct! +5 XP")
            update_progress(5, streak)
        else:
            st.error(f"Wrong. The correct answer is: {gq['answer']}")

# -------- Show Progress --------
st.markdown("---")
st.write(f"**XP:** {xp} | **Streak:** {streak} days | **Level:** {level.capitalize()}")

