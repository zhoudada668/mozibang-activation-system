#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MoziBang 激活码管理后台 - SQLite版本
提供激活码生成、管理、统计等功能
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
import sqlite3
import secrets
import string
import hashlib
from datetime import datetime, timedelta
import uuid
import os
from functools import wraps

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

# SQLite数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'mozibang_activation.db')

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 使结果可以像字典一样访问
    return conn

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def verify_password(stored_password, provided_password):
    """验证密码"""
    try:
        # 格式: pbkdf2:sha256:100000$salt$hash
        parts = stored_password.split('$')
        if len(parts) != 3:
            return False
            
        algorithm_info, salt, hash_value = parts
        
        # 解析算法信息: pbkdf2:sha256:100000
        algo_parts = algorithm_info.split(':')
        if len(algo_parts) != 3 or algo_parts[0] != 'pbkdf2' or algo_parts[1] != 'sha256':
            return False
            
        iterations = int(algo_parts[2])
        
        # 计算密码哈希
        password_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('utf-8'), iterations)
        return hash_value == password_hash.hex()
    except:
        return False

def generate_activation_code():
    """生成激活码"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(16))

def generate_batch_id():
    """生成批次ID"""
    return f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

@app.route('/')
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """仪表板"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取统计数据
        stats = {}
        
        # 激活码统计
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_used = 1 THEN 1 ELSE 0 END) as used,
                SUM(CASE WHEN is_used = 0 AND is_disabled = 0 THEN 1 ELSE 0 END) as unused
            FROM activation_codes
        """)
        code_result = cursor.fetchone()
        stats['total_codes'] = code_result[0] if code_result else 0
        stats['used_codes'] = code_result[1] if code_result else 0
        stats['unused_codes'] = code_result[2] if code_result else 0
        
        # Pro用户统计
        cursor.execute("SELECT COUNT(*) FROM pro_users WHERE is_active = 1")
        pro_users_result = cursor.fetchone()
        stats['pro_users'] = pro_users_result[0] if pro_users_result else 0
        
        # 激活码分类统计
        cursor.execute("""
            SELECT 
                code_type,
                COUNT(*) as total,
                SUM(CASE WHEN is_used = 1 THEN 1 ELSE 0 END) as used,
                SUM(CASE WHEN is_used = 0 AND is_disabled = 0 THEN 1 ELSE 0 END) as available
            FROM activation_codes 
            GROUP BY code_type
        """)
        code_stats = cursor.fetchall()
        
        # Pro用户分类统计
        cursor.execute("""
            SELECT 
                pro_type,
                COUNT(*) as total,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active
            FROM pro_users 
            GROUP BY pro_type
        """)
        user_stats = cursor.fetchall()
        
        # 最近激活记录
        cursor.execute("""
            SELECT user_email, pro_type, activated_at 
            FROM pro_users 
            ORDER BY activated_at DESC 
            LIMIT 10
        """)
        recent_activations = cursor.fetchall()
        
        conn.close()
        
        return render_template('dashboard.html', 
                             stats=stats,
                             code_stats=code_stats,
                             user_stats=user_stats,
                             recent_activations=recent_activations)
    except Exception as e:
        flash(f'获取统计数据失败: {str(e)}', 'error')
        # 返回空的统计数据以避免模板错误
        empty_stats = {
            'total_codes': 0,
            'used_codes': 0,
            'unused_codes': 0,
            'pro_users': 0
        }
        return render_template('dashboard.html', 
                             stats=empty_stats,
                             code_stats=[],
                             user_stats=[],
                             recent_activations=[])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('login.html')
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admin_users WHERE username = ? AND is_active = 1", (username,))
            admin = cursor.fetchone()
            
            if admin and verify_password(admin['password_hash'], password):
                session['admin_user'] = {
                    'id': admin['id'],
                    'username': admin['username'],
                    'role': admin['role']
                }
                
                # 更新登录信息
                cursor.execute("""
                    UPDATE admin_users 
                    SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1 
                    WHERE id = ?
                """, (admin['id'],))
                conn.commit()
                
                flash('登录成功', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('用户名或密码错误', 'error')
            
            conn.close()
        except Exception as e:
            flash(f'登录失败: {str(e)}', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """管理员登出"""
    session.pop('admin_user', None)
    flash('已安全退出', 'info')
    return redirect(url_for('login'))

@app.route('/statistics')
@login_required
def statistics():
    """统计报表页面"""
    try:
        # 导入统计模块
        import sys
        sys.path.append(os.path.dirname(__file__))
        from statistics_report import ActivationStatistics
        
        stats = ActivationStatistics()
        
        # 获取各种统计数据
        activation_overview = stats.get_activation_overview()
        user_stats = stats.get_user_statistics()
        daily_trends = stats.get_daily_activation_trends()
        revenue_estimation = stats.get_revenue_estimation()
        
        # 计算总收入
        total_revenue = sum(item['subtotal'] for item in revenue_estimation)
        
        # 获取最近激活用户
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_email, pro_type, activated_at 
            FROM pro_users 
            ORDER BY activated_at DESC 
            LIMIT 10
        """)
        recent_users = cursor.fetchall()
        
        # 获取即将过期用户
        cursor.execute("""
            SELECT 
                user_email,
                pro_type,
                expires_at,
                CAST((julianday(expires_at) - julianday('now')) AS INTEGER) as days_until_expiry
            FROM pro_users 
            WHERE expires_at IS NOT NULL 
                AND expires_at > datetime('now')
                AND is_active = 1
            ORDER BY expires_at ASC
            LIMIT 10
        """)
        expiring_users = cursor.fetchall()
        
        conn.close()
        
        return render_template('statistics.html',
                             activation_overview=activation_overview,
                             user_stats=user_stats,
                             daily_trends=daily_trends,
                             revenue_estimation=revenue_estimation,
                             total_revenue=total_revenue,
                             recent_users=recent_users,
                             expiring_users=expiring_users)
    except Exception as e:
        flash(f'获取统计数据失败: {str(e)}', 'error')
        return render_template('statistics.html')

@app.route('/api/export-report', methods=['POST'])
@login_required
def export_report():
    """导出统计报告API"""
    try:
        # 导入统计模块
        import sys
        sys.path.append(os.path.dirname(__file__))
        from statistics_report import ActivationStatistics
        
        stats = ActivationStatistics()
        filepath = stats.export_report_to_json()
        
        return jsonify({
            'success': True,
            'filepath': filepath,
            'message': '报告导出成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '报告导出失败'
        }), 500

@app.route('/codes')
@login_required
def codes():
    """激活码管理"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = 20
        code_type = request.args.get('type', '')
        status = request.args.get('status', '')
        
        # 构建查询条件
        where_conditions = []
        params = []
        
        if code_type:
            where_conditions.append("code_type = ?")
            params.append(code_type)
        
        if status == 'used':
            where_conditions.append("is_used = 1")
        elif status == 'available':
            where_conditions.append("is_used = 0 AND is_disabled = 0")
        elif status == 'disabled':
            where_conditions.append("is_disabled = 1")
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # 获取总数
        cursor.execute(f"SELECT COUNT(*) FROM activation_codes{where_clause}", params)
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        offset = (page - 1) * per_page
        cursor.execute(f"""
            SELECT * FROM activation_codes{where_clause} 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """, params + [per_page, offset])
        codes = cursor.fetchall()
        
        conn.close()
        
        # 计算分页信息
        total_pages = (total + per_page - 1) // per_page
        
        return render_template('codes.html', 
                             codes=codes,
                             page=page,
                             total_pages=total_pages,
                             total=total,
                             code_type=code_type,
                             status=status)
    except Exception as e:
        flash(f'获取激活码列表失败: {str(e)}', 'error')
        return render_template('codes.html', codes=[])

@app.route('/generate', methods=['GET', 'POST'])
@login_required
def generate():
    """生成激活码"""
    if request.method == 'POST':
        try:
            code_type = request.form.get('code_type')
            count = int(request.form.get('count', 1))
            batch_name = request.form.get('batch_name', '')
            notes = request.form.get('notes', '')
            
            if not code_type or count <= 0 or count > 1000:
                flash('参数错误', 'error')
                return render_template('generate.html')
            
            if not batch_name:
                batch_name = generate_batch_id()
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            generated_codes = []
            for _ in range(count):
                code = generate_activation_code()
                cursor.execute("""
                    INSERT INTO activation_codes (code, code_type, batch_name, notes)
                    VALUES (?, ?, ?, ?)
                """, (code, code_type, batch_name, notes))
                generated_codes.append(code)
            
            conn.commit()
            conn.close()
            
            flash(f'成功生成 {count} 个激活码', 'success')
            return render_template('generate.html', generated_codes=generated_codes)
            
        except Exception as e:
            flash(f'生成激活码失败: {str(e)}', 'error')
    
    return render_template('generate.html')

@app.route('/users')
@login_required
def users():
    """Pro用户管理"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = 20
        pro_type = request.args.get('type', '')
        status = request.args.get('status', '')
        
        # 构建查询条件
        where_conditions = []
        params = []
        
        if pro_type:
            where_conditions.append("pro_type = ?")
            params.append(pro_type)
        
        if status == 'active':
            where_conditions.append("is_active = 1")
        elif status == 'inactive':
            where_conditions.append("is_active = 0")
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # 获取总数
        cursor.execute(f"SELECT COUNT(*) FROM pro_users{where_clause}", params)
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        offset = (page - 1) * per_page
        cursor.execute(f"""
            SELECT * FROM pro_users{where_clause} 
            ORDER BY activated_at DESC 
            LIMIT ? OFFSET ?
        """, params + [per_page, offset])
        users = cursor.fetchall()
        
        conn.close()
        
        # 计算分页信息
        total_pages = (total + per_page - 1) // per_page
        
        return render_template('users.html', 
                             users=users,
                             page=page,
                             total_pages=total_pages,
                             total=total,
                             pro_type=pro_type,
                             status=status)
    except Exception as e:
        flash(f'获取用户列表失败: {str(e)}', 'error')
        return render_template('users.html', users=[])

@app.route('/api/disable_code', methods=['POST'])
@login_required
def disable_code():
    """禁用激活码"""
    try:
        data = request.get_json()
        code = data.get('code')
        reason = data.get('reason', '管理员禁用')
        
        if not code:
            return jsonify({'success': False, 'message': '激活码不能为空'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE activation_codes 
            SET is_disabled = 1, disabled_at = CURRENT_TIMESTAMP, disabled_reason = ?
            WHERE code = ? AND is_used = 0
        """, (reason, code))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': '激活码已禁用'})
        else:
            conn.close()
            return jsonify({'success': False, 'message': '激活码不存在或已被使用'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})

@app.route('/api/revoke_user', methods=['POST'])
@login_required
def revoke_user():
    """撤销用户Pro状态"""
    try:
        data = request.get_json()
        user_email = data.get('email')
        reason = data.get('reason', '管理员撤销')
        
        if not user_email:
            return jsonify({'success': False, 'message': '用户邮箱不能为空'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE pro_users 
            SET is_active = 0, revoked_at = CURRENT_TIMESTAMP, revoked_reason = ?
            WHERE user_email = ? AND is_active = 1
        """, (reason, user_email))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': '用户Pro状态已撤销'})
        else:
            conn.close()
            return jsonify({'success': False, 'message': '用户不存在或已被撤销'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})

# 创建模板文件夹
templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

if __name__ == '__main__':
    print("🚀 启动 MoziBang 激活码管理后台 (SQLite版本)")
    print(f"📁 数据库文件: {DB_PATH}")
    print("🌐 访问地址: http://localhost:5000")
    print("👤 默认账号: admin / admin123")
    app.run(host='0.0.0.0', port=5000, debug=True)