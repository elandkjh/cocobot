from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
from cocobot_web import get_response, recognize_image
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# SQLite 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('cocobot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, session_id TEXT, name TEXT, conversation_history TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET'])
def home():
    if 'session_id' not in session:
        session['session_id'] = request.cookies.get('session')
    if not session['session_id']:
        session['session_id'] = request.remote_addr
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    session_id = session['session_id']
    user_input = request.json.get('user_input')

    conn = sqlite3.connect('cocobot.db')
    c = conn.cursor()

    c.execute("SELECT name, conversation_history FROM users WHERE session_id=?", (session_id,))
    user_data = c.fetchone()

    if user_data:
        name, conversation_history = user_data
        if not name:
            if "이름" in user_input:
                name = user_input.split()[-1]
                conversation_history += f"User: {user_input}\n"
                response = f"반가워, {name}야! 나는 코코몽이라고 해. 무슨 얘기를 하고 싶니?"
                conversation_history += f"코코몽: {response}\n"
                c.execute("UPDATE users SET name=?, conversation_history=? WHERE session_id=?", (name, conversation_history, session_id))
            else:
                response = "만나서 반가워, 난 코코몽이라고 해. 넌 이름이 뭐니?"
        else:
            conversation_history += f"User: {user_input}\n"
            response = get_response(user_input, conversation_history)
            conversation_history += f"코코몽: {response}\n"
            c.execute("UPDATE users SET conversation_history=? WHERE session_id=?", (conversation_history, session_id))
    else:
        if "이름" in user_input:
            name = user_input.split()[-1]
            conversation_history = f"User: {user_input}\n"
            response = f"반가워, {name}야! 나는 코코몽이라고 해. 무슨 얘기를 하고 싶니?"
            conversation_history += f"코코몽: {response}\n"
            c.execute("INSERT INTO users (session_id, name, conversation_history) VALUES (?, ?, ?)", 
                      (session_id, name, conversation_history))
        else:
            response = "만나서 반가워, 난 코코몽이라고 해. 넌 이름이 뭐니?"
            c.execute("INSERT INTO users (session_id, name, conversation_history) VALUES (?, ?, ?)", 
                      (session_id, None, ""))

    conn.commit()
    conn.close()

    return jsonify({'response': response})

@app.route('/recognize', methods=['POST'])
def recognize():
    image = request.files['image']
    result = recognize_image(image)
    return render_template('result.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
