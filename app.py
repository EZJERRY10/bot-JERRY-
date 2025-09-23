# api/app.py
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from supabase import create_client, Client
import os
import io

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_secret_key_here")

# ربط الموقع بـ Supabase
supabase_url = "https://xqigepvcqbuidumcydlq.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhxaWdlcHZjcWJ1aWR1bWN5ZGxxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgxMTkxMDgsImV4cCI6MjA3MzY5NTEwOH0.fzMiC89n26uG29lX9SPl2E1RCibNaebwt9vNhj24jzQ"
supabase: Client = create_client(supabase_url, supabase_key)

# مسار للملفات الثابتة (مثل CSS)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/')
def index():
    mangas = []
    try:
        response = supabase.table("manga").select("*").execute()
        mangas = response.data
    except Exception as e:
        print(f"حدث خطأ في الاتصال بـ Supabase: {e}")
    return render_template('index.html', mangas=mangas)

# مسار لصفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = supabase.auth.sign_in_with_password({"email": email, "password": password})
            session['user'] = user.user.dict()
            return redirect(url_for('index'))
        except Exception as e:
            return render_template('login.html', error="فشل تسجيل الدخول. تأكد من البريد وكلمة المرور.")
    return render_template('login.html')

# مسار لصفحة تسجيل حساب جديد
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = supabase.auth.sign_up({"email": email, "password": password})
            session['user'] = user.user.dict()
            return redirect(url_for('index'))
        except Exception as e:
            return render_template('register.html', error="فشل تسجيل الحساب. تأكد من المعلومات.")
    return render_template('register.html')

# مسار لصفحة الرفع
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        manga_name = request.form['manga_name']
        chapter_number = request.form['chapter_number']
        images = request.files.getlist('images')
        
        if not images:
            return render_template('upload.html', message="الرجاء اختيار صورة واحدة على الأقل.", user=session['user'])
        
        image_urls = []
        try:
            for i, image_file in enumerate(images):
                file_path = f"manga/{manga_name}/{chapter_number}/{i+1}.png"
                image_data = image_file.read()
                supabase.storage.from_("manga-images").upload(file_path, image_data)
                public_url = supabase.storage.from_("manga-images").get_public_url(file_path)
                image_urls.append(public_url)
            
            chapter_info = {
                "manga_name": manga_name,
                "chapter_number": chapter_number,
                "images": image_urls,
                "published_at": None,
                "user_id": session['user']['id']
            }
            supabase.table("chapters").insert(chapter_info).execute()
            
            return render_template('upload.html', success="تم الرفع بنجاح!", user=session['user'])

        except Exception as e:
            print(f"حدث خطأ: {e}")
            return render_template('upload.html', error="حدث خطأ في عملية الرفع. الرجاء المحاولة مرة أخرى.", user=session['user'])
    
    return render_template('upload.html', user=session['user'])

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

