import streamlit as st
import requests
import random
import sqlite3
import tempfile
import os
import datetime
from gtts import gTTS

# -------- TRANSLATION TO KHMER --------
from deep_translator import GoogleTranslator

def translate_to_khmer(text):
    try:
        return GoogleTranslator(source='en', target='km').translate(text)
    except Exception as e:
        return f"⚠️ Error: {e}"

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
        #word_resp = requests.get("https://random-word-api.herokuapp.com/word?number=1")
        #if word_resp.status_code != 200:
            #st.warning("Failed to fetch a random word.")
            #return None
        #word = word_resp.json()[0] 

        vocab_list = [
            # --- Work / Office ---
            "desk", "computer", "keyboard", "mouse", "monitor", "chair", "meeting", "deadline", "project",
            "schedule", "email", "call", "conference", "team", "manager", "supervisor", "colleague",
            "presentation", "report", "document", "printer", "scanner", "notebook", "pen", "marker",
            "whiteboard", "laptop", "task", "goal", "plan", "strategy", "review", "feedback", "promotion",
            "interview", "resume", "salary", "bonus", "office", "cubicle", "workplace", "lunch break",
            "coffee", "tea", "focus", "deadline", "workflow", "software", "hardware",
        
            # --- Home / Household ---
            "house", "apartment", "room", "kitchen", "bathroom", "bedroom", "living room", "balcony",
            "garage", "garden", "furniture", "sofa", "table", "chair", "bed", "pillow", "blanket",
            "lamp", "window", "door", "curtain", "fan", "air conditioner", "heater", "vacuum", "broom",
            "mop", "cleaning", "laundry", "clothes", "washing machine", "dryer", "dishwasher", "fridge",
            "microwave", "stove", "oven", "toaster", "sink", "mirror", "toilet", "shower", "soap", "towel",
        
            # --- Travel / Transportation ---
            "car", "bus", "train", "plane", "airport", "station", "ticket", "passport", "visa", "luggage",
            "suitcase", "bag", "map", "hotel", "reservation", "tourist", "guide", "route", "destination",
            "taxi", "subway", "bike", "motorcycle", "driver", "license", "rental", "traffic", "road", "highway",
            "lane", "crosswalk", "sidewalk", "bridge", "tunnel", "schedule", "delay", "boarding", "gate",
            "arrival", "departure", "seat", "window seat", "aisle", "cruise", "ferry", "bus stop",
        
            # --- Sleep / Rest / Wellness ---
            "sleep", "nap", "rest", "relax", "bed", "pillow", "mattress", "blanket", "dream", "alarm",
            "clock", "tired", "exhausted", "snore", "sleepy", "doze", "bedtime", "night", "midnight",
            "sleep schedule", "deep sleep", "light sleep", "wake up", "yawn", "lullaby", "silence",
            "noise", "calm", "peaceful", "cozy", "warm", "dark", "light", "curtains", "fan", "sleepwear",
            "pajamas", "nightlight", "sleep mask", "sleeping bag", "comfort", "restless", "insomnia",
        
            # --- Eating / Food ---
            "eat", "drink", "food", "meal", "breakfast", "lunch", "dinner", "snack", "fruit", "vegetable",
            "meat", "chicken", "beef", "pork", "fish", "rice", "noodles", "bread", "butter", "cheese",
            "egg", "milk", "water", "juice", "tea", "coffee", "sugar", "salt", "pepper", "spoon", "fork",
            "knife", "plate", "bowl", "cup", "glass", "napkin", "table", "chair", "kitchen", "cook",
            "fry", "boil", "bake", "grill", "taste", "sweet", "sour", "salty", "bitter", "spicy", "hot",
            "cold", "hungry", "thirsty", "full", "delicious", "menu", "order", "bill", "tip", "waiter",
        
            # --- Shopping / Money ---
            "shop", "store", "supermarket", "mall", "market", "cart", "basket", "cash", "credit card",
            "receipt", "change", "price", "discount", "sale", "offer", "coupon", "buy", "sell", "spend",
            "pay", "money", "wallet", "purse", "ATM", "bank", "account", "deposit", "withdraw", "loan",
            "budget", "cost", "cheap", "expensive", "affordable", "worth", "value", "bill", "coin",
        
            # --- Daily Routine / Personal Care ---
            "wake", "shower", "brush", "toothbrush", "toothpaste", "soap", "shampoo", "conditioner",
            "towel", "comb", "mirror", "dress", "shirt", "pants", "shorts", "shoes", "socks", "jacket",
            "belt", "watch", "phone", "charger", "bag", "keys", "wallet", "umbrella", "raincoat", "hat",
            "glasses", "sunglasses", "makeup", "lotion", "perfume", "deodorant", "nail", "clipper", "bath",
            "hygiene", "clean", "wash", "dry", "iron", "fold", "organize", "schedule", "routine",
        
            # --- Emotions / Social ---
            "happy", "sad", "angry", "excited", "bored", "tired", "nervous", "scared", "surprised",
            "confused", "calm", "proud", "ashamed", "embarrassed", "kind", "mean", "friendly", "rude",
            "polite", "honest", "lie", "laugh", "cry", "smile", "hug", "kiss", "greet", "goodbye", "hello",
            "please", "thank you", "sorry", "excuse me", "congratulations", "cheer", "support", "trust",
        
            # --- Nature / Environment ---
            "sun", "moon", "star", "sky", "cloud", "rain", "snow", "wind", "storm", "fog", "tree",
            "flower", "grass", "bush", "forest", "river", "lake", "ocean", "mountain", "hill", "valley",
            "sand", "rock", "soil", "weather", "climate", "season", "spring", "summer", "autumn", "winter",
            "hot", "cold", "warm", "cool", "fresh", "natural", "wild", "plant", "animal", "bird", "fish",
            "insect", "dog", "cat", "pet", "farm", "zoo",
        
            # --- Education / Learning ---
            "school", "class", "teacher", "student", "lesson", "homework", "exam", "test", "study",
            "learn", "book", "pen", "pencil", "notebook", "paper", "desk", "blackboard", "chalk",
            "subject", "math", "science", "history", "geography", "language", "English", "dictionary",
            "translate", "understand", "question", "answer", "grade", "score", "pass", "fail", "classmate",
            "principal", "uniform", "library", "read", "write", "spell", "repeat", "practice", "memorize"
        ]


        # Step 2: Pick a random word
        word = random.choice(vocab_list)

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

    # Translate the word to Khmer
    translation_word = translate_to_khmer(word)
    st.markdown(f"**ភាសាខ្មែរ:** {translation_word}")
    
    # Use st.audio for reliable playback
    audio_bytes = tts_audio(word)
    st.audio(audio_bytes, format="audio/mp3")

    st.markdown(f"**Meaning:** {meaning}")

    # Use st.audio for reliable playback
    audio_bytes_meaning = tts_audio(meaning)
    st.audio(audio_bytes_meaning, format="audio/mp3")

    # Translate the meaning to Khmer
    khmer_translation = translate_to_khmer(meaning)
    st.markdown(f"**អត្ថន័យ:** {khmer_translation}")
    
    st.markdown(f"*Example:* _{example}_")

    # Use st.audio for reliable playback
    audio_bytes_example = tts_audio(example)
    st.audio(audio_bytes_example, format="audio/mp3")

    # Translate the example to Khmer
    translation_example = translate_to_khmer(example)
    st.markdown(f"**ឧទាហរណ៍:** {translation_example}")

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














