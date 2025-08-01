import streamlit as st
import random, requests, tempfile, base64, sqlite3, datetime
from gtts import gTTS

# Initialize DB:
conn = sqlite3.connect("progress.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS progress (date TEXT PRIMARY KEY, xp INTEGER, streak INTEGER)")
conn.commit()

# Vocabulary pool (read from file or built-in)
word_pool = ["apple","run","book","happy","dog","challenge","improve","travel","meticulous","ubiquitous","candid"]

# Utility functions:
def get_word_data(word):
    resp = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
    if resp.status_code != 200:
        return None
    data = resp.json()[0]
    # take first meaning and example
    meaning = data["meanings"][0]["definitions"][0]["definition"]
    example = data["meanings"][0]["definitions"][0].get("example","")
    return meaning, example

def tts_audio(word):
    tts = gTTS(text=word, lang="en")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        audio = open(fp.name,"rb").read()
    os.unlink(fp.name)
    b64 = base64.b64encode(audio).decode()
    return f"<audio controls autoplay><source src='data:audio/mp3;base64,{b64}' type='audio/mp3'></audio>"

def get_progress():
    today = datetime.date.today().isoformat()
    r = conn.execute("SELECT xp, streak FROM progress WHERE date=?", (today,)).fetchone()
    return r if r else (0,0)

def update_progress(xp_delta, streak):
    today = datetime.date.today().isoformat()
    xp, _ = get_progress()
    conn.execute("INSERT OR REPLACE INTO progress (date, xp, streak) VALUES (?, ?, ?)",
                 (today, xp + xp_delta, streak))
    conn.commit()

def get_streak():
    r = conn.execute("SELECT date, streak FROM progress ORDER BY date DESC LIMIT 1").fetchone()
    if r and r[0] == (datetime.date.today() - datetime.timedelta(days=1)).isoformat():
        return r[1] + 1
    return 1

def get_level(xp):
    return "Beginner" if xp < 20 else "Intermediate" if xp < 50 else "Advanced"

# App UI:
st.title("🧠 Vocab Practice Powered by DictionaryAPI")
xp, _ = get_progress()
streak = get_streak()
st.info(f"Level: {get_level(xp)} • XP: {xp} • Streak: {streak} days")

if "word" not in st.session_state:
    st.session_state.word = random.choice(word_pool)

word = st.session_state.word
wd = get_word_data(word)
if not wd:
    st.error(f"No definition found for '{word}'.")
else:
    meaning, example = wd
    st.header(word.capitalize())
    st.markdown(tts_audio(word), unsafe_allow_html=True)
    st.write(f"**Meaning:** {meaning}")
    if example:
        st.write(f"_Example:_ {example}")

    choices = [meaning]
    while len(choices) < 4:
        m = get_word_data(random.choice(word_pool))
        if m:
            choices.append(m[0])
    random.shuffle(choices)

    choice = st.selectbox("Choose the correct meaning:", choices)
    if st.button("Submit"):
        if choice == meaning:
            st.success("✅ Correct! +5 XP")
            update_progress(5, streak)
        else:
            st.error(f"❌ Incorrect. Answer: {meaning}")
        st.session_state.word = random.choice(word_pool)
        st.experimental_rerun()

st.markdown("---")
