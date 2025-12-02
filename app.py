from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit

# --- НАЛАШТУВАННЯ ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey123' # Ключ для сесій
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///webapp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# WebSockets (Пункт 14)
socketio = SocketIO(app, async_mode='eventlet')

# --- БАЗА ДАНИХ (МОДЕЛІ) ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False) # У реальному житті треба хешувати!

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Зв'язок з юзером

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- МАРШРУТИ (ROUTES) ---

@app.route('/')
def home():
    # Пункт 2: Домашня сторінка (Спорт інвентар)
    return render_template('index.html')

@app.route('/about')
def about():
    # Пункт 3: Сторінка про нас
    return render_template('about.html')

@app.route('/form', methods=['GET', 'POST'])
def form():
    # Пункт 4: Форма з привітанням
    name = None
    if request.method == 'POST':
        name = request.form.get('name')
    return render_template('form.html', name=name)

# --- АВТОРИЗАЦІЯ (Пункт 10) ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Такий користувач вже існує')
            return redirect(url_for('register'))
        
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('tasks'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('tasks'))
        flash('Невірний логін або пароль')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- ЗАВДАННЯ (CRUD) (Пункти 5-9) ---

@app.route('/tasks', methods=['GET', 'POST'])
@login_required # Тільки для авторизованих
def tasks():
    if request.method == 'POST':
        title = request.form.get('title')
        new_task = Task(title=title, user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()
        # Push-сповіщення через WebSockets (Пункт 15)
        socketio.emit('new_task_notification', {'message': f'Нове завдання: {title}'})
        return redirect(url_for('tasks'))

    user_tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks.html', tasks=user_tasks)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    task = Task.query.get_or_404(id)
    if task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('tasks'))

@app.route('/update/<int:id>')
@login_required
def update(id):
    task = Task.query.get_or_404(id)
    if task.user_id == current_user.id:
        task.status = not task.status
        db.session.commit()
    return redirect(url_for('tasks'))

# --- RESTful API (Пункт 11) ---

@app.route('/api/tasks', methods=['GET'])
def api_tasks():
    tasks = Task.query.all()
    return jsonify([{'id': t.id, 'title': t.title, 'status': t.status} for t in tasks])

# --- ЗАПУСК ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Створення БД при запуску
    socketio.run(app, host='0.0.0.0', port=5000)
