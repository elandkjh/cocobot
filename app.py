from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
from cocobot_web import get_response
import sqlite3
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# SQLite 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('cocobot.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            session_id TEXT,
            name TEXT,
            birthday TEXT,
            age TEXT,
            gender TEXT,
            hobbies TEXT,
            favorite_music TEXT,
            favorite_food TEXT,
            conversation_history TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def extract_information(user_input):
    # 생일 추출
    birthday_match = re.search(r'(\d{1,2})[월/.-](\d{1,2})[일]?', user_input)
    if birthday_match:
        birthday = f"{birthday_match.group(1).zfill(2)}/{birthday_match.group(2).zfill(2)}"
    else:
        birthday = None

    # 성별 추출
    gender_match = re.search(r'(남자|여자|남성|여성|남|여)', user_input)
    if gender_match:
        gender = '남' if gender_match.group(0) in ['남자', '남성', '남'] else '여'
    else:
        gender = None

    # 좋아하는 음악 추출
    music_match = re.findall(r'(\w+)\s?[-]\s?(\w+)', user_input)
    favorite_music = ', '.join([f"{m[0]}-{m[1]}" for m in music_match]) if music_match else None

    # 좋아하는 취미, 음식 추출 (단순 키워드로 예시)
    hobbies = None
    favorite_food = None

    if '취미' in user_input:
        hobbies = user_input.split('취미')[1].strip().split()[0]

    if '음식' in user_input:
        favorite_food = user_input.split('음식')[1].strip().split()[0]

    return birthday, gender, hobbies, favorite_music, favorite_food

@app.route('/', methods=['GET'])
def home():
    if 'session_id' not in session:
        session['session_id'] = request.cookies.get('session')
    if not session['session_id']:
        session['session_id'] = request.remote_addr
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    if 'session_id' not in session:
        session['session_id'] = request.cookies.get('session')
    if not session['session_id']:
        session['session_id'] = request.remote_addr

    session_id = session['session_id']
    user_input = request.json.get('user_input')

    conn = sqlite3.connect('cocobot.db')
    c = conn.cursor()

    c.execute("SELECT name, birthday, age, gender, hobbies, favorite_music, favorite_food, conversation_history FROM users WHERE session_id=?", (session_id,))
    user_data = c.fetchone()

    if user_data:
        name, birthday, age, gender, hobbies, favorite_music, favorite_food, conversation_history = user_data

        # 입력에서 정보 추출
        new_birthday, new_gender, new_hobbies, new_favorite_music, new_favorite_food = extract_information(user_input)
        updates = []
        if new_birthday and not birthday:
            birthday = new_birthday
            updates.append("birthday")
        if new_gender and not gender:
            gender = new_gender
            updates.append("gender")
        if new_hobbies and not hobbies:
            hobbies = new_hobbies
            updates.append("hobbies")
        if new_favorite_music and not favorite_music:
            favorite_music = new_favorite_music
            updates.append("favorite_music")
        if new_favorite_food and not favorite_food:
            favorite_food = new_favorite_food
            updates.append("favorite_food")

        conversation_history += f"User: {user_input}\n"
        if updates:
            update_string = ", ".join(updates)
            response = f"{name}, 너의 {update_string}을(를) 기억할게!"
        else:
            response = get_response(user_input, conversation_history, name, birthday, age, gender, hobbies, favorite_music, favorite_food)
        conversation_history += f"{response}\n"

        c.execute("UPDATE users SET birthday=?, age=?, gender=?, hobbies=?, favorite_music=?, favorite_food=?, conversation_history=? WHERE session_id=?", 
                  (birthday, age, gender, hobbies, favorite_music, favorite_food, conversation_history, session_id))
    else:
        if "이름" in user_input:
            name = user_input.split()[-1]
            conversation_history = f"User: {user_input}\n"
            response = f"반가워, {name}야! 나는 코코몽이라고 해. 무슨 얘기를 하고 싶니?"
            conversation_history += f"{response}\n"
            c.execute("INSERT INTO users (session_id, name, conversation_history) VALUES (?, ?, ?)", 
                      (session_id, name, conversation_history))
        else:
            response = "만나서 반가워, 난 코코몽이라고 해. 넌 이름이 뭐니?"
            c.execute("INSERT INTO users (session_id, name, conversation_history) VALUES (?, ?, ?)", 
                      (session_id, None, ""))

    conn.commit()
    conn.close()

    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)
