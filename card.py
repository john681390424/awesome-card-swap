# card.py

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from google.oauth2 import id_token
from google.auth.transport import requests

app = Flask(__name__)
app.secret_key = "your_secret_key"  # 设置用于会话加密的密钥

# 配置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = 'your_database_connection_string'
db = SQLAlchemy(app)

# 定义数据库模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)

class TradingCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('trading_cards', lazy=True))

# 路由：首页
@app.route('/')
def index():
    trading_cards = TradingCard.query.all()
    return render_template('index.html', trading_cards=trading_cards)

# 路由：登录
@app.route('/login')
def login():
    # 在此处实现Google OAuth认证逻辑
    return redirect(url_for('index'))

# 路由：注销
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

# 路由：上传交换卡片
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        user_id = session['user_id']

        trading_card = TradingCard(title=title, description=description, user_id=user_id)
        db.session.add(trading_card)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('upload.html')

# 路由：Google OAuth回调
@app.route('/oauth_callback')
def oauth_callback():
    # 在此处实现Google OAuth回调逻辑
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

# 路由：用户注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # 检查用户是否已存在
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('该邮箱已被注册，请使用其他邮箱。', 'error')
            return redirect(url_for('register'))

        # 创建新用户
        new_user = User(email=email, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        flash('注册成功，请登录。', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# 路由：用户个人页面
@app.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    trading_cards = TradingCard.query.filter_by(user_id=user_id).all()
    return render_template('user_profile.html', user=user, trading_cards=trading_cards)

# 路由：搜索交换卡片
@app.route('/search')
def search():
    keyword = request.args.get('keyword')
    trading_cards = TradingCard.query.filter(
        (TradingCard.title.like(f'%{keyword}%')) |
        (TradingCard.description.like(f'%{keyword}%'))
    ).all()
    return render_template('search_results.html', keyword=keyword, trading_cards=trading_cards)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    trading_card_id = db.Column(db.Integer, db.ForeignKey('trading_card.id'), nullable=False)
    trading_card = db.relationship('TradingCard', backref=db.backref('comments', lazy=True))

# 路由：添加评论
@app.route('/trading_card/<int:trading_card_id>/add_comment', methods=['POST'])
def add_comment(trading_card_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    text = request.form['comment']

    comment = Comment(text=text, user_id=user_id, trading_card_id=trading_card_id)
    db.session.add(comment)
    db.session.commit()

    return redirect(url_for('trading_card_details', trading_card_id=trading_card_id))

from werkzeug.utils import secure_filename
import os

# 配置图片上传路径
app.config['UPLOAD_FOLDER'] = 'path_to_upload_folder'

# 路由：上传交换卡片
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        user_id = session['user_id']
        image_file = request.files['image']

# 路由：管理员审核交换卡片
@app.route('/admin/approve_trading_card/<int:trading_card_id>', methods=['POST'])
def approve_trading_card(trading_card_id):
    if 'user_id' not in session or not is_admin(session['user_id']):
        return redirect(url_for('login'))

    trading_card = TradingCard.query.get_or_404(trading_card_id)
    trading_card.approved = True
    db.session.commit()

    flash('交换卡片已审核通过。', 'success')
    return redirect(url_for('admin_dashboard'))

def is_admin(user_id):
    user = User.query.get(user_id)
    return user.is_admin

# 路由：管理员面板
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or not is_admin(session['user_id']):
        return redirect(url_for('login'))

    trading_cards = TradingCard.query.all()
    return render_template('admin_dashboard.html', trading_cards=trading_cards)

