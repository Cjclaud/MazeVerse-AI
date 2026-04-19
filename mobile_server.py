from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

players = {}
race_started = False
race_finished = False
winner = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MAZEVERSE | Knowledge Uplink</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        :root { --cyan: #00f5ff; --blue: #3a69eb; --dark: #040612; --glass: rgba(10, 16, 40, 0.95); --pink: #ff50be; --success: #00ff95; }
        body {
            background-color: var(--dark);
            background-image: radial-gradient(circle at center, #0a1028 0%, #040612 100%);
            color: #f0f7ff; font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0;
            display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; overflow: hidden; user-select: none;
        }
        #game-container {
            width: 90%; max-width: 420px; padding: 25px 15px; border: 1px solid rgba(0, 245, 255, 0.3);
            border-radius: 30px; background: var(--glass); backdrop-filter: blur(10px); box-shadow: 0 0 30px rgba(0, 245, 255, 0.1);
        }
        h1 { color: var(--cyan); font-size: 24px; letter-spacing: 3px; margin-bottom: 20px; text-shadow: 0 0 10px var(--cyan); }
        .btn { background: linear-gradient(135deg, var(--cyan) 0%, var(--blue) 100%); border: none; color: white; padding: 18px; font-size: 18px; font-weight: bold; border-radius: 15px; cursor: pointer; width: 100%; touch-action: manipulation; }
        
        #maze-grid { 
            display: grid; grid-template-columns: repeat(10, 1fr); gap: 1px; 
            background: #1a2a4a; border: 2px solid var(--blue); border-radius: 8px; 
            margin: 15px auto; width: 280px; height: 280px; padding: 2px;
        }
        .cell { width: 100%; height: 100%; border-radius: 2px; }
        .wall { background: #0a1530; }
        .path { background: #0f1c3d; }
        .player { background: var(--cyan); border-radius: 50%; box-shadow: 0 0 10px var(--cyan); transform: scale(0.8); }
        .goal { background: var(--pink); box-shadow: 0 0 10px var(--pink); border-radius: 4px; transform: scale(0.9); }
        
        #controls { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; width: 160px; margin: 15px auto; }
        .control-btn { background: rgba(70, 135, 255, 0.2); border: 1px solid var(--blue); color: var(--cyan); height: 50px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }

        .option-btn { display: block; width: 100%; padding: 12px; margin: 8px 0; background: rgba(255,255,255,0.05); border: 1px solid var(--blue); color: white; border-radius: 10px; text-align: left; font-size: 14px; }
        #feedback-emoji { font-size: 60px; margin: 10px; height: 70px; }
    </style>
</head>
<body>
    <div id="game-container">
        <h1 id="main-title">MAZEVERSE</h1>
        
        <div id="setup">
            <input type="text" id="player-name" style="padding:15px; width:80%; border-radius:10px; margin-bottom:20px;" placeholder="CALLSIGN">
            <button class="btn" onclick="joinGame()">INITIALIZE</button>
        </div>

        <div id="lobby" style="display: none;">
            <p>SYNCING PILOTS...</p>
            <p id="player-count" style="font-size: 48px; color: var(--cyan);">1</p>
        </div>

        <div id="race" style="display: none;">
            <p style="font-size:12px">STEP 1: REACH THE CORE</p>
            <div id="maze-grid"></div>
            <div id="controls">
                <div></div><div class="control-btn" onclick="move(0, -1)">▲</div><div></div>
                <div class="control-btn" onclick="move(-1, 0)">◀</div><div></div><div class="control-btn" onclick="move(1, 0)">▶</div>
                <div></div><div class="control-btn" onclick="move(0, 1)">▼</div><div></div>
            </div>
        </div>

        <div id="quiz" style="display: none;">
            <p style="font-size:12px; color:var(--cyan)">STEP 2: KNOWLEDGE UPLINK</p>
            <div id="feedback-emoji"></div>
            <p id="q-text" style="font-size:16px; font-weight:bold;"></p>
            <div id="options-box"></div>
            <p id="q-count" style="font-size:12px; margin-top:10px"></p>
        </div>

        <div id="results" style="display: none;">
            <h2 id="res-msg" style="color:var(--success)">MISSION COMPLETE</h2>
            <p id="winner-display"></p>
        </div>
    </div>

    <script>
        const socket = io();
        let myName = "", maze = [], playerPos = {x: 0, y: 0}, quizMarks = 0, raceMarks = 0;
        
        function generateSimpleMaze() {
            let m = Array(10).fill().map(() => Array(10).fill(1));
            function carve(x, y) {
                m[y][x] = 0;
                let dirs = [[0,1],[0,-1],[1,0],[-1,0]].sort(() => Math.random() - 0.5);
                for(let [dx, dy] of dirs) {
                    let nx = x + dx*2, ny = y + dy*2;
                    if(nx>=0 && nx<10 && ny>=0 && ny<10 && m[ny][nx] === 1) {
                        m[y+dy][x+dx] = 0; carve(nx, ny);
                    }
                }
            }
            carve(0, 0); m[9][9] = 0; m[8][9] = 0; return m;
        }

        function drawMaze() {
            const grid = document.getElementById('maze-grid'); grid.innerHTML = '';
            for(let y=0; y<10; y++) {
                for(let x=0; x<10; x++) {
                    let cell = document.createElement('div');
                    cell.className = 'cell ' + (maze[y][x] === 1 ? 'wall' : 'path');
                    if(x === playerPos.x && y === playerPos.y) cell.classList.add('player');
                    else if(x === 9 && y === 9) cell.classList.add('goal');
                    grid.appendChild(cell);
                }
            }
        }

        function move(dx, dy) {
            let nx = playerPos.x + dx, ny = playerPos.y + dy;
            if(nx>=0 && nx<10 && ny>=0 && ny<10 && maze[ny][nx] === 0) {
                playerPos.x = nx; playerPos.y = ny; drawMaze();
                if(nx === 9 && ny === 9) { raceMarks = 50; startQuiz(); }
            }
        }

        const questions = [
            { q: "What does BFS stand for?", a: ["Breadth-First Search", "Basic Flow System", "Best Find Strategy"], c: 0 },
            { q: "Which algorithm uses Heuristics?", a: ["Dijkstra", "A* Search", "Linear Scan"], c: 1 },
            { q: "A Heuristic is best described as...", a: ["An exact math rule", "An educated guess", "A type of virus"], c: 1 },
            { q: "DFS explores as deep as possible before backtracking.", a: ["True", "False"], c: 0 },
            { q: "Which search finds the shortest path in unweighted grids?", a: ["BFS", "DFS", "Random Walk"], c: 0 }
        ];
        let currentQ = 0;

        function startQuiz() {
            document.getElementById('race').style.display = 'none';
            document.getElementById('quiz').style.display = 'block';
            showQuestion();
        }

        function showQuestion() {
            const q = questions[currentQ];
            document.getElementById('q-text').innerText = q.q;
            document.getElementById('q-count').innerText = "Question " + (currentQ+1) + " of 5";
            const box = document.getElementById('options-box'); box.innerHTML = '';
            q.a.forEach((opt, i) => {
                let b = document.createElement('button'); b.className = 'option-btn';
                b.innerText = opt; b.onclick = () => checkAnswer(i); box.appendChild(b);
            });
        }

        function checkAnswer(idx) {
            const feedback = document.getElementById('feedback-emoji');
            if(idx === questions[currentQ].c) { quizMarks += 10; feedback.innerText = "😊"; }
            else { feedback.innerText = "😢"; }
            
            setTimeout(() => {
                feedback.innerText = "";
                currentQ++;
                if(currentQ >= questions.length) finishAll();
                else showQuestion();
            }, 1000);
        }

        function finishAll() {
            const total = raceMarks + quizMarks;
            socket.emit('finish', {name: myName, race_marks: raceMarks, quiz_marks: quizMarks, total: total});
            document.getElementById('quiz').style.display = 'none';
            document.getElementById('results').style.display = 'block';
            document.getElementById('winner-display').innerText = "Final Score: " + total + "/100";
        }

        function joinGame() {
            myName = document.getElementById('player-name').value.trim().toUpperCase() || "STUDENT";
            socket.emit('join', {name: myName});
            document.getElementById('setup').style.display = 'none';
            document.getElementById('lobby').style.display = 'block';
        }

        socket.on('player_update', (count) => { document.getElementById('player-count').innerText = count; });
        socket.on('race_start', () => {
            maze = generateSimpleMaze(); document.getElementById('lobby').style.display = 'none';
            document.getElementById('race').style.display = 'block'; drawMaze();
        });
        socket.on('winner_announced', (w) => {
            document.getElementById('race').style.display = 'none';
            document.getElementById('quiz').style.display = 'none';
            document.getElementById('results').style.display = 'block';
            document.getElementById('res-msg').innerText = (w.name === myName) ? "VICTORY" : "RACE OVER";
            document.getElementById('winner-display').innerText = "Winner: " + w.name + " (" + w.total + " Marks)";
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE)

@socketio.on('join')
def handle_join(data):
    players[request.sid] = {'name': data['name'], 'finished': False}
    emit('player_update', len(players), broadcast=True)

@socketio.on('finish')
def handle_finish(data):
    global winner, race_finished
    if race_finished: return
    winner = data
    race_finished = True
    emit('winner_announced', winner, broadcast=True)

def run_server(host='0.0.0.0', port=8000):
    socketio.run(app, host=host, port=port, debug=False, use_reloader=False)

def start_background_server():
    threading.Thread(target=run_server, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)
