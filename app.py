from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from bson import ObjectId
from pymongo import MongoClient
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = 'guclu-bir-sifre-uret-burada'  # Bunu daha güvenli bir şifreyle değiştir
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'avi', 'webm'}

ADMIN_PASSWORD = '12345'  # Girişte kullanılacak sabit şifre

# MongoDB Atlas bağlantısı
client = MongoClient("mongodb+srv://admin:gucluSifre123@cluster0.b3e3zuv.mongodb.net/villa_galerisi?retryWrites=true&w=majority&appName=Cluster0")
db = client['villa_galerisi']
projects_col = db['projects']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    projects = list(projects_col.find())
    for project in projects:
        project['_id'] = str(project['_id'])
    return render_template('index.html', projects=projects)

# -------------------- LOGIN --------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Şifre hatalı!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

def login_required(func):
    from functools import wraps
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return decorated_function
# -----------------------------------------------

@app.route('/admin')
@login_required
def admin():
    projects = list(projects_col.find())
    for p in projects:
        p['_id'] = str(p['_id'])
        p['media_count'] = len(p.get('media', []))
    return render_template('admin.html', projects=projects)

@app.route('/admin/add', methods=['POST'])
@login_required
def add_project():
    name = request.form['project_name']
    files = request.files.getlist('media_files')
    media_paths = []

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            media_paths.append(filename)

    project = {'name': name, 'media': media_paths}
    projects_col.insert_one(project)
    return redirect(url_for('admin'))

@app.route('/admin/delete/<project_id>')
@login_required
def delete_project(project_id):
    project = projects_col.find_one({'_id': ObjectId(project_id)})
    if project:
        for file in project.get('media', []):
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
            except Exception:
                pass
        projects_col.delete_one({'_id': ObjectId(project_id)})
    return redirect(url_for('admin'))

@app.route('/admin/edit/<project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = projects_col.find_one({'_id': ObjectId(project_id)})
    if not project:
        return redirect(url_for('admin'))

    if request.method == 'POST':
        files = request.files.getlist('media_files')
        media_paths = project.get('media', [])

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                media_paths.append(filename)

        projects_col.update_one({'_id': ObjectId(project_id)}, {'$set': {'media': media_paths}})
        return redirect(url_for('admin'))

    project['_id'] = str(project['_id'])
    return render_template('edit.html', project=project)

@app.route('/admin/<project_id>/remove/<filename>', methods=['POST'])
@login_required
def remove_media(project_id, filename):
    project = projects_col.find_one({'_id': ObjectId(project_id)})
    if not project:
        return redirect(url_for('admin'))

    media_list = project.get('media', [])
    if filename in media_list:
        media_list.remove(filename)
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        except Exception:
            pass
        projects_col.update_one({'_id': ObjectId(project_id)}, {'$set': {'media': media_list}})
    
    return redirect(url_for('edit_project', project_id=project_id))

if __name__ == '__main__':
    app.run(debug=True)
