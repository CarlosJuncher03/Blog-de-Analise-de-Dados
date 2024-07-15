import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import os
from conector import inserir_dados, executar_query, atualizar_dados
from werkzeug.utils import secure_filename
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['HEADER_UPLOAD_FOLDER'] = 'static/cabecalho'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['HEADER_UPLOAD_FOLDER']):
    os.makedirs(app.config['HEADER_UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def create_default_admin():
    query = "SELECT * FROM users WHERE username = %s"
    result = executar_query(query, ('admin',))
    if not result:
        password_hash = generate_password_hash('admin')
        query = "INSERT INTO users (username, email, password_hash, name, user_level) VALUES (%s, %s, %s, %s, %s)"
        inserir_dados(query, ('admin', 'admin@example.com', password_hash, 'Administrator', 2))
        print('Default admin user created.')

@app.before_request
def before_request():
    create_default_admin()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash('Todos os campos são obrigatórios.')
            return render_template('login.html')

        query = "SELECT * FROM users WHERE username = %s"
        result = executar_query(query, (username,))
        if result:
            user_data = result[0]
            if user_data['is_active']:  # Verifica se o usuário está ativo
                if check_password_hash(user_data['password_hash'], password):
                    session['user_id'] = user_data['id']
                    session['username'] = user_data['username']
                    session['user_level'] = user_data['user_level']  # Adiciona o user_level na sessão
                    flash('Login bem-sucedido!')
                    return redirect(url_for('home'))
                else:
                    flash('Nome de usuário ou senha inválidos')
            else:
                flash('Usuário está inativo. Por favor, contate o administrador.')
        else:
            flash('Nome de usuário ou senha inválidos')

        return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Você foi desconectado.')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Verifica se o usuário tem nível 2
    if 'user_level' not in session or session['user_level'] != 2:
        flash('Você não tem permissão para acessar esta página.')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        password2 = request.form['password2']
        user_level = request.form['user_level']
        
        if not username or not email or not name or not password or not password2 or not user_level:
            flash('Todos os campos são obrigatórios.')
            return render_template('register.html')
        
        if password != password2:
            flash('As senhas não coincidem.')
            return render_template('register.html')
        
        result_username = executar_query("SELECT * FROM users WHERE username = %s", (username,))
        if result_username:
            flash('Por favor, use um nome de usuário diferente.')
            return render_template('register.html')
        
        result_email = executar_query("SELECT * FROM users WHERE email = %s", (email,))
        if result_email:
            flash('Por favor, use um endereço de email diferente.')
            return render_template('register.html')

        password_hash = generate_password_hash(password)
        query = "INSERT INTO users (username, email, password_hash, name, user_level) VALUES (%s, %s, %s, %s, %s)"
        if inserir_dados(query, (username, email, password_hash, name, user_level)):
            flash('Parabéns, você se registrou com sucesso!')
            return redirect(url_for('login'))
        else:
            flash('Falha no registro. Por favor, tente novamente.')
    return render_template('register.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    posts_query = """
        SELECT posts.id, posts.title, posts.content, users.name as author, posts.created_at, header_image_filename
        FROM posts 
        JOIN users ON posts.author_id = users.id 
        LEFT JOIN post_visibility ON posts.id = post_visibility.post_id
        WHERE posts.author_id = %s OR post_visibility.user_id = %s
        GROUP BY posts.id, posts.title, posts.content, users.name, posts.created_at, header_image_filename
        ORDER BY posts.created_at DESC
        LIMIT 10
    """
    posts = executar_query(posts_query, (user_id, user_id))
    
    programs = [
        {'name': 'Pentaho', 'image': 'pentaho.jpg', 'description': 'Ferramenta de integração de dados e análise de negócios.'},
        {'name': 'Apache Hop', 'image': 'apache_hop.jpg', 'description': 'Ferramenta de orquestração e pipeline de dados.'},
        {'name': 'Power BI', 'image': 'power_bi.jpg', 'description': 'Ferramenta de visualização e análise de dados da Microsoft.'},
        {'name': 'Metabase', 'image': 'metabase.jpg', 'description': 'Plataforma de BI de código aberto.'},
        {'name': 'Excel', 'image': 'excel.jpg', 'description': 'Software de planilha da Microsoft para análise de dados.'},
        {'name': 'Crystal Reports', 'image': 'crystal_reports.jpg', 'description': 'Ferramenta de relatório da SAP.'},
        {'name': 'Armazem de dados', 'image': 'database.jpg', 'description': 'Soluções de armazenamento de dados.'},
        {'name': 'Apache Kafka', 'image': 'apache_kafka.jpg', 'description': 'Plataforma de streaming de eventos distribuída.'},
    ]
    
    return render_template('home.html', username=session['username'], posts=posts, programs=programs)

@app.route('/full_editor')
def full_editor():
    if 'user_id' not in session or session.get('user_level') != 2:
        return redirect(url_for('home'))

    title = request.args.get('title', '')
    content = request.args.get('content', '')
    return render_template('full_editor.html', title=title, content=content)

@app.route('/get_selected_users', methods=['GET'])
def get_selected_users():
    post_id = request.args.get('post_id')
    query = request.args.get('query', '')
    
    if post_id:
        if query:
            all_users = executar_query("SELECT id, name FROM users WHERE name LIKE %s", ('%' + query + '%',))
        else:
            all_users = executar_query("SELECT id, name FROM users")
        
        selected_users = executar_query("SELECT user_id FROM post_visibility WHERE post_id = %s", (post_id,))
        selected_user_ids = [user['user_id'] for user in selected_users]

        for user in all_users:
            user['selected'] = user['id'] in selected_user_ids

        return jsonify({'users': all_users})
    return jsonify({'users': []})

@app.route('/save_visibility', methods=['POST'])
def save_visibility():
    data = request.json
    post_id = data.get('post_id')
    user_ids = data.get('user_ids')

    if post_id is not None:
        if user_ids:
            inserir_dados("DELETE FROM post_visibility WHERE post_id = %s AND user_id NOT IN (%s)", (post_id, ', '.join(map(str, user_ids))))

            for user_id in user_ids:
                inserir_dados("INSERT INTO post_visibility (post_id, user_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE post_id=VALUES(post_id), user_id=VALUES(user_id)", (post_id, user_id))
        else:
            inserir_dados("DELETE FROM post_visibility WHERE post_id = %s", (post_id,))
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400

@app.route('/upload_header_image', methods=['POST'])
def upload_header_image():
    if 'header_image' not in request.files:
        return jsonify({'filename': None}), 400

    header_image = request.files['header_image']

    if header_image and allowed_file(header_image.filename):
        filename = secure_filename(header_image.filename)
        header_image.save(os.path.join(app.config['HEADER_UPLOAD_FOLDER'], filename))
        return jsonify({'filename': filename}), 200
    else:
        return jsonify({'filename': None}), 400

@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('user_level') != 2:
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        document = request.files.get('document')
        image = request.files.get('image')
        header_image = request.form.get('header_image', '')

        document_filename = None
        image_filename = None

        if document and allowed_file(document.filename):
            document_filename = secure_filename(document.filename)
            document.save(os.path.join(app.config['UPLOAD_FOLDER'], document_filename))

        if image and allowed_file(image.filename):
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        author_id = session['user_id']
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        query = """
            INSERT INTO posts (title, content, document_filename, image_filename, header_image_filename, author_id, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        if inserir_dados(query, (title, content, document_filename, image_filename, header_image, author_id, created_at)):
            flash('Postagem adicionada com sucesso!')
            return redirect(url_for('posts'))
        else:
            flash('Falha ao adicionar a postagem. Por favor, tente novamente.')

    return render_template('add_post.html')

@app.route('/posts')
def posts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    per_page = 10
    title_filter = request.args.get('title', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = """
        SELECT posts.id, posts.title, users.name as author, posts.created_at 
        FROM posts 
        JOIN users ON posts.author_id = users.id
        LEFT JOIN post_visibility ON posts.id = post_visibility.post_id
        WHERE (posts.author_id = %s OR post_visibility.user_id = %s)
        AND posts.title LIKE %s
    """
    
    params = [user_id, user_id, '%' + title_filter + '%']
    if start_date and end_date:
        query += " AND posts.created_at BETWEEN %s AND %s"
        params.extend([start_date, end_date])
    elif start_date:
        query += " AND posts.created_at >= %s"
        params.append(start_date)
    elif end_date:
        query += " AND posts.created_at <= %s"
        params.append(end_date)

    query += " GROUP BY posts.id, posts.title, users.name, posts.created_at ORDER BY posts.created_at DESC LIMIT %s OFFSET %s"
    params.extend([per_page, (page - 1) * per_page])

    posts = executar_query(query, params)

    total_query = """
        SELECT COUNT(DISTINCT posts.id) as 'total' 
        FROM posts 
        JOIN users ON posts.author_id = users.id
        LEFT JOIN post_visibility ON posts.id = post_visibility.post_id
        WHERE (posts.author_id = %s OR post_visibility.user_id = %s)
        AND posts.title LIKE %s
    """
    
    total_params = [user_id, user_id, '%' + title_filter + '%']
    if start_date and end_date:
        total_query += " AND posts.created_at BETWEEN %s AND %s"
        total_params.extend([start_date, end_date])
    elif start_date:
        total_query += " AND posts.created_at >= %s"
        total_params.append(start_date)
    elif end_date:
        total_query += " AND posts.created_at <= %s"
        total_params.append(end_date)

    total_result = executar_query(total_query, total_params)
    total_posts = total_result[0]['total'] if total_result and total_result[0] else 0
    total_pages = (total_posts // per_page) + (1 if total_posts % per_page > 0 else 0)

    return render_template('posts.html', posts=posts, page=page, total_pages=total_pages, title_filter=title_filter, start_date=start_date, end_date=end_date)

@app.route('/post/<int:post_id>')
def post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    query = """
        SELECT posts.*, users.name as author 
        FROM posts 
        JOIN users ON posts.author_id = users.id 
        LEFT JOIN post_visibility ON posts.id = post_visibility.post_id
        WHERE posts.id = %s AND (posts.author_id = %s OR post_visibility.user_id = %s)
    """
    post = executar_query(query, (post_id, user_id, user_id))
    if not post:
        flash('Postagem não encontrada.')
        return redirect(url_for('posts'))
    return render_template('post.html', post=post[0])

@app.route('/edit_post/<int:post_id>')
def edit_post(post_id):
    query = """
        SELECT posts.*, users.name as author 
        FROM posts 
        JOIN users ON posts.author_id = users.id 
        WHERE posts.id = %s
    """
    post = executar_query(query, (post_id,))
    if not post:
        flash('Postagem não encontrada.')
        return redirect(url_for('posts'))
    return render_template('edit_post.html', post=post[0])

@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    query = "DELETE FROM posts WHERE id = %s"
    if atualizar_dados(query, (post_id,)):
        flash('Postagem excluída com sucesso!')
    else:
        flash('Falha ao excluir a postagem.')
    return redirect(url_for('posts'))

@app.route('/update_post/<int:post_id>', methods=['POST'])
def update_post(post_id):
    title = request.form['title']
    content = request.form['content']

    query = """
        UPDATE posts 
        SET title = %s, content = %s
        WHERE id = %s
    """
    if inserir_dados(query, (title, content, post_id)):
        flash('Postagem atualizada com sucesso!')
    else:
        flash('Falha ao atualizar a postagem.')
    return redirect(url_for('posts'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']

        if password and password2 and password == password2:
            password_hash = generate_password_hash(password)
            query = """
                UPDATE users 
                SET name = %s, email = %s, password_hash = %s
                WHERE id = %s
            """
            params = (name, email, password_hash, user_id)
        else:
            query = """
                UPDATE users 
                SET name = %s, email = %s
                WHERE id = %s
            """
            params = (name, email, user_id)

        if inserir_dados(query, params):
            flash('Perfil atualizado com sucesso!')
        else:
            flash('Falha ao atualizar o perfil. Por favor, tente novamente.')
        return redirect(url_for('profile'))

    query = "SELECT * FROM users WHERE id = %s"
    user = executar_query(query, (user_id,))[0]
    return render_template('profile.html', user=user)

@app.route('/annotations', methods=['GET', 'POST'])
def annotations():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']

    if request.method == 'POST':
        title = request.form['title']
        post_id = request.form['post_id']
        comment = request.form['comment']
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        query = """
            INSERT INTO annotations (title, post_id, comment, user_id, created_at) 
            VALUES (%s, %s, %s, %s, %s)
        """
        if inserir_dados(query, (title, post_id, comment, user_id, created_at)):
            flash('Anotação adicionada com sucesso!')
        else:
            flash('Falha ao adicionar anotação.')
        return redirect(url_for('annotations'))
    
    title_filter = request.args.get('title', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = """
        SELECT annotations.id, annotations.title, annotations.comment, posts.title as post_title, annotations.user_id, annotations.created_at 
        FROM annotations 
        JOIN posts ON annotations.post_id = posts.id
        WHERE annotations.user_id = %s AND annotations.title LIKE %s
    """
    params = [user_id, '%' + title_filter + '%']
    if start_date and end_date:
        query += " AND annotations.created_at BETWEEN %s AND %s"
        params.extend([start_date, end_date])
    elif start_date:
        query += " AND annotations.created_at >= %s"
        params.append(start_date)
    elif end_date:
        query += " AND annotations.created_at <= %s"
        params.append(end_date)

    query += " ORDER BY annotations.created_at DESC"
    annotations = executar_query(query, params)

    posts_query = """
        SELECT DISTINCT posts.id, posts.title 
        FROM posts 
        LEFT JOIN post_visibility ON posts.id = post_visibility.post_id 
        WHERE posts.author_id = %s OR post_visibility.user_id = %s
    """
    posts = executar_query(posts_query, (user_id, user_id))

    return render_template('annotations.html', annotations=annotations, posts=posts, title_filter=title_filter, start_date=start_date, end_date=end_date)

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'filename': filename}), 200
    return jsonify({'error': 'File not allowed'}), 400

@app.route('/add_annotation', methods=['POST'])
def add_annotation():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    title = request.form['title']
    post_id = request.form['post_id']
    comment = request.form['comment']
    user_id = session['user_id']
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    query = """
        INSERT INTO annotations (title, post_id, comment, user_id, created_at) 
        VALUES (%s, %s, %s, %s, %s)
    """
    if inserir_dados(query, (title, post_id, comment, user_id, created_at)):
        flash('Anotação adicionada com sucesso!')
    else:
        flash('Falha ao adicionar anotação.')
    return redirect(url_for('annotations'))

@app.route('/delete_annotation/<int:annotation_id>')
def delete_annotation(annotation_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    query = "DELETE FROM annotations WHERE id = %s"
    if inserir_dados(query, (annotation_id,)):
        flash('Anotação excluída com sucesso!')
    else:
        flash('Falha ao excluir a anotação.')
    return redirect(url_for('annotations'))

@app.route('/edit_annotation/<int:annotation_id>', methods=['POST'])
def edit_annotation(annotation_id):
    title = request.form['title']
    post_id = request.form['post_id']
    comment = request.form['comment']

    query = """
        UPDATE annotations 
        SET title = %s, post_id = %s, comment = %s
        WHERE id = %s
    """
    if inserir_dados(query, (title, post_id, comment, annotation_id)):
        flash('Anotação atualizada com sucesso!')
    else:
        flash('Falha ao atualizar a anotação.')
    return redirect(url_for('annotations'))

@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    if 'user_level' not in session or session['user_level'] != 2:
        flash('Você não tem permissão para acessar esta página.')
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        password2 = request.form['password2']
        user_level = request.form['user_level']
        
        if not all([username, email, name, password, password2, user_level]):
            flash('Todos os campos são obrigatórios.')
            return redirect(url_for('manage_users'))

        if password != password2:
            flash('As senhas não coincidem.')
            return redirect(url_for('manage_users'))

        result_username = executar_query("SELECT * FROM users WHERE username = %s", (username,))
        if result_username:
            flash('Por favor, use um nome de usuário diferente.')
            return redirect(url_for('manage_users'))

        result_email = executar_query("SELECT * FROM users WHERE email = %s", (email,))
        if result_email:
            flash('Por favor, use um endereço de email diferente.')
            return redirect(url_for('manage_users'))

        password_hash = generate_password_hash(password)
        query = "INSERT INTO users (username, email, password_hash, name, user_level) VALUES (%s, %s, %s, %s, %s)"
        if inserir_dados(query, (username, email, password_hash, name, user_level)):
            flash('Usuário adicionado com sucesso!')
        else:
            flash('Falha ao adicionar usuário. Por favor, tente novamente.')

    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    per_page = 5
    offset = (page - 1) * per_page

    users_query = """
        SELECT id, username, email, name, user_level, is_active 
        FROM users
        WHERE username LIKE %s
        LIMIT %s OFFSET %s
    """
    users = executar_query(users_query, ('%' + search_query + '%', per_page, offset))

    total_query = """
        SELECT COUNT(*) as total 
        FROM users
        WHERE username LIKE %s
    """
    total_result = executar_query(total_query, ('%' + search_query + '%',))
    total_users = total_result[0]['total'] if total_result else 0
    total_pages = (total_users // per_page) + (1 if total_users % per_page > 0 else 0)

    return render_template('manage_users.html', users=users, page=page, total_pages=total_pages, search_query=search_query)

@app.route('/toggle_user/<int:user_id>')
def toggle_user(user_id):
    if 'user_level' not in session or session['user_level'] != 2:
        flash('Você não tem permissão para acessar esta página.')
        return redirect(url_for('home'))

    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')

    user = executar_query("SELECT is_active FROM users WHERE id = %s", (user_id,))
    if user:
        is_active = not user[0]['is_active']
        query = "UPDATE users SET is_active = %s WHERE id = %s"
        if atualizar_dados(query, (int(is_active), user_id)):
            flash('Status do usuário atualizado com sucesso!')
        else:
            flash('Falha ao atualizar status do usuário.')
    else:
        flash('Usuário não encontrado.')
    
    return redirect(url_for('manage_users', page=page, search=search_query))

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    query = """
        SELECT de.*
        FROM dashboard_entries de
        LEFT JOIN dashboard_visibility dv ON de.id = dv.entry_id
        WHERE (de.title LIKE %s OR de.description LIKE %s)
        AND (de.author_id = %s OR dv.user_id = %s)
        GROUP BY de.id
        LIMIT %s OFFSET %s
    """
    dashboard_entries = executar_query(query, ('%' + search_query + '%', '%' + search_query + '%', user_id, user_id, per_page, (page - 1) * per_page))
    
    total_query = """
        SELECT COUNT(DISTINCT de.id) as total
        FROM dashboard_entries de
        LEFT JOIN dashboard_visibility dv ON de.id = dv.entry_id
        WHERE (de.title LIKE %s OR de.description LIKE %s)
        AND (de.author_id = %s OR dv.user_id = %s)
    """
    total_result = executar_query(total_query, ('%' + search_query + '%', '%' + search_query + '%', user_id, user_id))
    total_entries = total_result[0]['total'] if total_result and total_result[0] else 0
    total_pages = (total_entries // per_page) + (1 if total_entries % per_page > 0 else 0)
    
    return render_template('dashboard.html', dashboard_entries=dashboard_entries, page=page, total_pages=total_pages, search_query=search_query)

@app.route('/add_dashboard_entry', methods=['POST'])
def add_dashboard_entry():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    title = request.form['title']
    link = request.form['link']
    description = request.form['description']
    
    query = "INSERT INTO dashboard_entries (title, link, description, author_id) VALUES (%s, %s, %s, %s)"
    if inserir_dados(query, (title, link, description, user_id)):
        flash('Entrada adicionada com sucesso!')
    else:
        flash('Falha ao adicionar entrada. Por favor, tente novamente.')
    
    return redirect(url_for('dashboard'))

@app.route('/edit_dashboard_entry/<int:entry_id>', methods=['POST'])
def edit_dashboard_entry(entry_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    title = request.form['title']
    link = request.form['link']
    description = request.form['description']
    
    query = "UPDATE dashboard_entries SET title = %s, link = %s, description = %s WHERE id = %s AND author_id = %s"
    if inserir_dados(query, (title, link, description, entry_id, user_id)):
        flash('Entrada editada com sucesso!')
    else:
        flash('Falha ao editar entrada. Por favor, tente novamente.')
    
    return redirect(url_for('dashboard'))

@app.route('/delete_dashboard_entry/<int:entry_id>')
def delete_dashboard_entry(entry_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    query = "DELETE FROM dashboard_entries WHERE id = %s"
    if atualizar_dados(query, (entry_id,)):
        flash('Entrada excluída com sucesso!')
    else:
        flash('Falha ao excluir entrada.')
    return redirect(url_for('dashboard'))

@app.route('/assign_users', methods=['POST'])
def assign_users():
    data = request.get_json()
    entry_id = data.get('entry_id')
    user_ids = data.get('user_ids')

    if entry_id is not None:
        if user_ids:
            inserir_dados("DELETE FROM dashboard_visibility WHERE entry_id = %s AND user_id NOT IN (%s)", (entry_id, ', '.join(map(str, user_ids))))

            for user_id in user_ids:
                inserir_dados("INSERT INTO dashboard_visibility (entry_id, user_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE entry_id=VALUES(entry_id), user_id=VALUES(user_id)", (entry_id, user_id))
        else:
            inserir_dados("DELETE FROM dashboard_visibility WHERE entry_id = %s", (entry_id,))
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400

@app.route('/edit_user', methods=['POST'])
def edit_user():
    user_id = request.form['user_id']
    username = request.form['username']
    email = request.form['email']
    name = request.form['name']
    password = request.form['password']
    password2 = request.form['password2']
    user_level = request.form['user_level']

    if not all([user_id, username, email, name, user_level]):
        flash('Todos os campos são obrigatórios, exceto a senha.')
        return redirect(url_for('manage_users'))

    if password and password != password2:
        flash('As senhas não coincidem.')
        return redirect(url_for('manage_users'))

    try:
        if password:
            password_hash = generate_password_hash(password)
            query = """
                UPDATE users 
                SET username = %s, email = %s, name = %s, password_hash = %s, user_level = %s
                WHERE id = %s
            """
            params = (username, email, name, password_hash, user_level, user_id)
        else:
            query = """
                UPDATE users 
                SET username = %s, email = %s, name = %s, user_level = %s
                WHERE id = %s
            """
            params = (username, email, name, user_level, user_id)

        if atualizar_dados(query, params):
            flash('Usuário atualizado com sucesso!')
        else:
            flash('Falha ao atualizar usuário.')
    except Exception as e:
        flash(f'Erro ao atualizar usuário: {e}')

    return redirect(url_for('manage_users'))


@app.route('/search_users/<int:entry_id>', methods=['GET'])
def search_users(entry_id):
    query = request.args.get('query', '')
    
    all_users = executar_query("SELECT id, name FROM users WHERE name LIKE %s", ('%' + query + '%',))
    selected_users = executar_query("SELECT user_id FROM dashboard_visibility WHERE entry_id = %s", (entry_id,))
    selected_user_ids = [user['user_id'] for user in selected_users]
    
    for user in all_users:
        user['selected'] = user['id'] in selected_user_ids
    
    return jsonify(all_users)

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=8000)
