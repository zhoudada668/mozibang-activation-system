#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MoziBang 激活码管理后台
提供激活码生成、管理、统计等功能
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
import pymysql
import secrets
import string
import hashlib
from datetime import datetime, timedelta
import uuid
import os
from functools import wraps
from statistics_report import ActivationStatistics

app = Flask(__name__)
app.secret_key = 'mozibang-admin-secret-key-2024'  # 生产环境应使用环境变量
CORS(app)

# 添加moment模板过滤器和全局函数
@app.template_filter('moment')
def moment_filter(dt):
    """moment过滤器，用于格式化时间"""
    if dt:
        return dt
    return datetime.now()

@app.template_global()
def moment():
    """全局模板函数，返回当前时间的datetime对象"""
    return datetime.now()

# 添加datetime到模板上下文
@app.context_processor
def inject_datetime():
    return {'datetime': datetime, 'moment': datetime.now()}

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # 空密码，根据实际情况修改
    'database': 'mozibang_activation',
    'charset': 'utf8mb4'
}

# 管理员账号配置（简单实现，生产环境应使用数据库）
ADMIN_USERS = {
    'admin': 'admin123',  # 用户名: 密码
    'manager': 'manager123'
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_activation_code():
    """生成激活码"""
    # 生成格式: MOZIBANG-PRO-XXXX-XXXX
    part1 = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    part2 = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    return f"MOZIBANG-PRO-{part1}-{part2}"

def generate_batch_id():
    """生成批次ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    return f"BATCH_{timestamp}_{random_suffix}"

@app.route('/')
@login_required
def dashboard():
    """管理后台首页"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取统计数据
        stats = {}
        
        # 总激活码数量
        cursor.execute("SELECT COUNT(*) as total FROM activation_codes")
        stats['total_codes'] = cursor.fetchone()['total']
        
        # 已使用激活码数量
        cursor.execute("SELECT COUNT(*) as used FROM activation_codes WHERE status = 'used'")
        stats['used_codes'] = cursor.fetchone()['used']
        
        # 未使用激活码数量
        cursor.execute("SELECT COUNT(*) as unused FROM activation_codes WHERE status = 'unused'")
        stats['unused_codes'] = cursor.fetchone()['unused']
        
        # Pro用户数量
        cursor.execute("SELECT COUNT(*) as pro_users FROM user_pro_status WHERE is_pro = 1")
        stats['pro_users'] = cursor.fetchone()['pro_users']
        
        # 最近7天激活数量
        cursor.execute("""
            SELECT COUNT(*) as recent_activations 
            FROM activation_codes 
            WHERE status = 'used' AND used_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        stats['recent_activations'] = cursor.fetchone()['recent_activations']
        
        cursor.close()
        conn.close()
        
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        flash(f'获取统计数据失败: {str(e)}', 'error')
        return render_template('dashboard.html', stats={})

@app.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in ADMIN_USERS and ADMIN_USERS[username] == password:
            session['admin_user'] = username
            flash('登录成功', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """管理员登出"""
    session.pop('admin_user', None)
    flash('已退出登录', 'info')
    return redirect(url_for('login'))

@app.route('/codes')
@login_required
def codes_list():
    """激活码列表页面"""
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取激活码列表
        cursor.execute("""
            SELECT ac.*, ab.batch_name 
            FROM activation_codes ac
            LEFT JOIN activation_batches ab ON ac.batch_id = ab.batch_id
            ORDER BY ac.created_at DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        codes = cursor.fetchall()
        
        # 获取总数量
        cursor.execute("SELECT COUNT(*) as total FROM activation_codes")
        total = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()
        
        # 计算分页信息
        total_pages = (total + per_page - 1) // per_page
        
        return render_template('codes_list.html', 
                             codes=codes, 
                             page=page, 
                             total_pages=total_pages,
                             total=total)
    except Exception as e:
        flash(f'获取激活码列表失败: {str(e)}', 'error')
        return render_template('codes_list.html', codes=[], page=1, total_pages=1, total=0)

@app.route('/generate', methods=['GET', 'POST'])
@login_required
def generate_codes():
    """生成激活码页面"""
    if request.method == 'POST':
        try:
            count = int(request.form.get('count', 1))
            code_type = request.form.get('code_type', 'pro_lifetime')
            batch_name = request.form.get('batch_name', '')
            notes = request.form.get('notes', '')
            
            if count <= 0 or count > 1000:
                flash('激活码数量必须在1-1000之间', 'error')
                return render_template('generate_codes.html')
            
            # 生成批次ID
            batch_id = generate_batch_id()
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 创建批次记录
            cursor.execute("""
                INSERT INTO activation_batches (batch_id, batch_name, code_type, total_count, created_by, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (batch_id, batch_name, code_type, count, session['admin_user'], notes))
            
            # 生成激活码
            generated_codes = []
            for i in range(count):
                code = generate_activation_code()
                cursor.execute("""
                    INSERT INTO activation_codes (code, code_type, batch_id, notes)
                    VALUES (%s, %s, %s, %s)
                """, (code, code_type, batch_id, f'批次生成 - {batch_name}'))
                generated_codes.append(code)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash(f'成功生成 {count} 个激活码', 'success')
            return render_template('generate_result.html', 
                                 codes=generated_codes, 
                                 batch_id=batch_id,
                                 batch_name=batch_name)
            
        except Exception as e:
            flash(f'生成激活码失败: {str(e)}', 'error')
    
    return render_template('generate_codes.html')

@app.route('/users')
@login_required
def users_list():
    """Pro用户列表页面"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT ups.*, ac.code as activation_code_used
            FROM user_pro_status ups
            LEFT JOIN activation_codes ac ON ups.activation_code = ac.code
            WHERE ups.is_pro = 1
            ORDER BY ups.activated_at DESC
        """)
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('users_list.html', users=users)
    except Exception as e:
        flash(f'获取用户列表失败: {str(e)}', 'error')
        return render_template('users_list.html', users=[])

@app.route('/api/disable_code', methods=['POST'])
@login_required
def disable_code():
    """禁用激活码API"""
    try:
        code = request.json.get('code')
        if not code:
            return jsonify({'success': False, 'message': '激活码不能为空'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE activation_codes 
            SET status = 'disabled' 
            WHERE code = %s AND status = 'unused'
        """, (code,))
        
        if cursor.rowcount > 0:
            conn.commit()
            result = {'success': True, 'message': '激活码已禁用'}
        else:
            result = {'success': False, 'message': '激活码不存在或已被使用'}
        
        cursor.close()
        conn.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})

@app.route('/api/statistics')
@login_required
def api_statistics():
    """获取统计数据API"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 按日期统计激活数量（最近30天）
        cursor.execute("""
            SELECT DATE(used_at) as date, COUNT(*) as count
            FROM activation_codes 
            WHERE status = 'used' AND used_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(used_at)
            ORDER BY date
        """)
        daily_activations = cursor.fetchall()
        
        # 按类型统计激活码
        cursor.execute("""
            SELECT code_type, status, COUNT(*) as count
            FROM activation_codes
            GROUP BY code_type, status
        """)
        type_stats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'daily_activations': daily_activations,
            'type_stats': type_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/statistics')
@login_required
def statistics():
    """统计报表页面"""
    try:
        # 使用MySQL连接创建统计对象
        stats = ActivationStatistics(get_db_connection())
        
        # 获取统计数据
        daily_trends = stats.get_daily_activation_trend(days=30)
        code_stats = stats.get_code_type_distribution()
        user_activity = stats.get_user_activity_report()
        
        return render_template('statistics.html', 
                             daily_trends=daily_trends,
                             code_stats=code_stats,
                             user_activity=user_activity)
    except Exception as e:
        flash(f'获取统计数据失败: {str(e)}', 'error')
        return render_template('statistics.html', 
                             daily_trends=[],
                             code_stats=[],
                             user_activity=[])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)