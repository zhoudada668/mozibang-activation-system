#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MoziBang 激活码验证API + 管理后台 - SQLite版本
提供激活码验证、Pro状态管理、管理后台等功能
"""

import sqlite3
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_cors import CORS
import os
import logging

app = Flask(__name__)

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

# 配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mozibang-secret-key-2024')
API_SECRET_KEY = os.environ.get('API_SECRET_KEY', 'mozibang_api_secret_2024')

# CORS配置 - 生产环境应限制来源
if os.environ.get('FLASK_ENV') == 'production':
    CORS(app, origins=['chrome-extension://*'])
else:
    CORS(app)  # 开发环境允许所有来源

# SQLite数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'mozibang_activation.db')

# 管理员账户配置
ADMIN_USERS = {
    'admin': 'admin123'
}

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_user' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def init_database():
    """初始化数据库表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建激活码表 - 使用与代码匹配的字段名
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activation_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            code_type TEXT NOT NULL DEFAULT 'pro_lifetime',
            batch_name TEXT DEFAULT NULL,
            notes TEXT DEFAULT NULL,
            is_used BOOLEAN DEFAULT FALSE,
            used_by TEXT DEFAULT NULL,
            used_at DATETIME DEFAULT NULL,
            is_disabled BOOLEAN DEFAULT FALSE,
            disabled_at DATETIME DEFAULT NULL,
            disabled_reason TEXT DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            token TEXT UNIQUE NOT NULL,
            pro_status TEXT NOT NULL DEFAULT 'inactive',
            pro_activated_at DATETIME,
            pro_expires_at DATETIME,
            activation_code TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_type ON activation_codes(code_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_batch_name ON activation_codes(batch_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_is_used ON activation_codes(is_used)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_is_disabled ON activation_codes(is_disabled)')
    
    # 插入一些测试激活码
    test_codes = [
        ('MOZIBANG-PRO-2024', 'pro_lifetime', 'TEST-BATCH-001'),
        ('TEST-CODE-123', 'pro_1year', 'TEST-BATCH-001'),
        ('DEMO-ACTIVATION', 'pro_6month', 'TEST-BATCH-001')
    ]
    
    for code, code_type, batch_name in test_codes:
        cursor.execute('''
            INSERT OR IGNORE INTO activation_codes (code, code_type, batch_name, notes)
            VALUES (?, ?, ?, ?)
        ''', (code, code_type, batch_name, '测试激活码'))
    
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 使结果可以像字典一样访问
    return conn

def verify_api_key(f):
    """API密钥验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_SECRET_KEY:
            return jsonify({
                'success': False,
                'message': 'Invalid API key',
                'error_code': 'INVALID_API_KEY'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def generate_user_token(user_email):
    """生成用户令牌"""
    return hashlib.sha256(f"{user_email}_{datetime.now().isoformat()}".encode()).hexdigest()

def generate_activation_code():
    """生成激活码"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(16))

def generate_batch_id():
    """生成批次ID"""
    return f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'sqlite',
        'database_file': DB_PATH
    })

@app.route('/api/fix_database', methods=['POST'])
@verify_api_key
def fix_database():
    """修复数据库 - 创建缺失的表"""
    try:
        from auto_create_pro_users import create_pro_users_table
        success = create_pro_users_table()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Database tables fixed successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to fix database tables',
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Database fix error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/activate', methods=['POST'])
@verify_api_key
def activate_code():
    """激活码验证和激活"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid JSON data',
                'error_code': 'INVALID_DATA'
            }), 400
        
        activation_code = data.get('activation_code', '').strip().upper()
        user_email = data.get('user_email', '').strip().lower()
        user_name = data.get('user_name', '').strip()
        
        if not activation_code or not user_email:
            return jsonify({
                'success': False,
                'message': 'Activation code and user email are required',
                'error_code': 'MISSING_REQUIRED_FIELDS'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查激活码是否存在且可用
        cursor.execute("""
            SELECT * FROM activation_codes 
            WHERE code = ? AND is_used = 0 AND is_disabled = 0
        """, (activation_code,))
        code_record = cursor.fetchone()
        
        if not code_record:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Invalid or already used activation code',
                'error_code': 'INVALID_CODE'
            }), 400
        
        # 检查用户是否已经是Pro用户
        cursor.execute("SELECT * FROM users WHERE email = ?", (user_email,))
        existing_user = cursor.fetchone()
        
        if existing_user and existing_user[3] == 'active':  # pro_status字段
            conn.close()
            return jsonify({
                'success': False,
                'message': 'User already has active Pro status',
                'error_code': 'ALREADY_PRO_USER'
            }), 400
        
        # 计算过期时间
        expires_at = None
        is_lifetime = False
        
        if code_record[2] == 'pro_lifetime':  # code_type字段
            is_lifetime = True
        elif code_record[2] == 'pro_1year':
            expires_at = (datetime.now() + timedelta(days=365)).isoformat()
        elif code_record[2] == 'pro_6month':
            expires_at = (datetime.now() + timedelta(days=180)).isoformat()
        else:
            # 默认为1年
            expires_at = (datetime.now() + timedelta(days=365)).isoformat()
        
        # 生成用户令牌
        user_token = generate_user_token(user_email)
        
        # 开始事务
        try:
            # 标记激活码为已使用
            cursor.execute("""
                UPDATE activation_codes 
                SET is_used = 1, used_by = ?, used_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE code = ?
            """, (user_email, activation_code))
            
            # 添加或更新用户记录
            if existing_user:
                cursor.execute("""
                    UPDATE users 
                    SET pro_status = 'active', pro_activated_at = CURRENT_TIMESTAMP,
                        pro_expires_at = ?, activation_code = ?, token = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE email = ?
                """, (expires_at, activation_code, user_token, user_email))
            else:
                cursor.execute("""
                    INSERT INTO users 
                    (email, token, pro_status, pro_activated_at, pro_expires_at, activation_code)
                    VALUES (?, ?, 'active', CURRENT_TIMESTAMP, ?, ?)
                """, (user_email, user_token, expires_at, activation_code))
            
            conn.commit()
            
            print(f"Activation successful: {user_email} -> {activation_code}")
            
            return jsonify({
                'success': True,
                'message': 'Activation successful',
                'data': {
                    'user_email': user_email,
                    'pro_type': code_record[2],  # code_type字段
                    'is_lifetime': is_lifetime,
                    'expires_at': expires_at,
                    'user_token': user_token,
                    'activated_at': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            conn.rollback()
            raise e
            
    except Exception as e:
        print(f"Activation error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/check', methods=['POST'])
@verify_api_key
def check_code():
    """检查激活码状态"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid JSON data',
                'error_code': 'INVALID_DATA'
            }), 400
        
        activation_code = data.get('code', '').strip().upper()
        
        if not activation_code:
            return jsonify({
                'success': False,
                'message': 'Activation code is required',
                'error_code': 'MISSING_CODE'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查激活码是否存在
        cursor.execute("""
            SELECT code, code_type, is_used, is_disabled, used_by, used_at, created_at
            FROM activation_codes 
            WHERE code = ?
        """, (activation_code,))
        code_record = cursor.fetchone()
        
        if not code_record:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Activation code not found',
                'error_code': 'CODE_NOT_FOUND'
            }), 404
        
        # 返回激活码状态信息
        return jsonify({
            'success': True,
            'data': {
                'code': code_record[0],
                'code_type': code_record[1],
                'is_used': bool(code_record[2]),
                'is_disabled': bool(code_record[3]),
                'used_by': code_record[4],
                'used_at': code_record[5],
                'created_at': code_record[6],
                'is_available': not code_record[2] and not code_record[3]  # 未使用且未禁用
            }
        })
        
    except Exception as e:
        print(f"Check code error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/verify_pro', methods=['POST'])
@verify_api_key
def verify_pro_status():
    """验证用户Pro状态"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid JSON data',
                'error_code': 'INVALID_DATA'
            }), 400
        
        user_email = data.get('user_email', '').strip().lower()
        user_token = data.get('user_token', '').strip()
        
        if not user_email:
            return jsonify({
                'success': False,
                'message': 'User email is required',
                'error_code': 'MISSING_USER_EMAIL'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询用户Pro状态
        cursor.execute("""
            SELECT * FROM users 
            WHERE email = ? AND pro_status = 'active'
        """, (user_email,))
        user_record = cursor.fetchone()
        
        if not user_record:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'User not found or not active',
                'error_code': 'USER_NOT_FOUND',
                'is_pro': False
            })
        
        # 检查是否过期（如果不是终身版）
        is_expired = False
        if user_record['pro_expires_at']:
            expires_at = datetime.fromisoformat(user_record['pro_expires_at'])
            if expires_at < datetime.now():
                is_expired = True
        
        # 更新最后登录时间
        cursor.execute("""
            UPDATE users 
            SET updated_at = CURRENT_TIMESTAMP 
            WHERE email = ?
        """, (user_email,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Pro status verified',
            'data': {
                'is_pro': not is_expired,
                'pro_type': 'pro',
                'is_lifetime': user_record['pro_expires_at'] is None,
                'expires_at': user_record['pro_expires_at'],
                'activated_at': user_record['pro_activated_at'],
                'is_expired': is_expired,
                'last_login': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        print(f"Pro status verification error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/stats', methods=['GET'])
@verify_api_key
def get_stats():
    """获取系统统计信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 激活码统计
        cursor.execute("""
            SELECT 
                type,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'used' THEN 1 ELSE 0 END) as used,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as available
            FROM activation_codes 
            GROUP BY type
        """)
        code_stats = [dict(row) for row in cursor.fetchall()]
        
        # Pro用户统计
        cursor.execute("""
            SELECT 
                'pro' as pro_type,
                COUNT(*) as total,
                SUM(CASE WHEN pro_status = 'active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN pro_status = 'inactive' THEN 1 ELSE 0 END) as inactive
            FROM users 
        """)
        user_stats = [dict(row) for row in cursor.fetchall()]
        
        # 总体统计
        cursor.execute("SELECT COUNT(*) as total FROM activation_codes")
        total_codes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE pro_status = 'active'")
        total_active_users = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'activation_codes': code_stats,
                'pro_users': user_stats,
                'summary': {
                    'total_codes': total_codes,
                    'total_active_users': total_active_users
                }
            }
        })
        
    except Exception as e:
        print(f"Stats error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/revoke_pro', methods=['POST'])
@verify_api_key
def revoke_pro_status():
    """撤销用户Pro状态"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid JSON data',
                'error_code': 'INVALID_DATA'
            }), 400
        
        user_email = data.get('user_email', '').strip().lower()
        reason = data.get('reason', 'API revocation')
        
        if not user_email:
            return jsonify({
                'success': False,
                'message': 'User email is required',
                'error_code': 'MISSING_USER_EMAIL'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users 
            SET pro_status = 'inactive', updated_at = CURRENT_TIMESTAMP
            WHERE email = ? AND pro_status = 'active'
        """, (user_email,))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            
            print(f"Pro status revoked: {user_email}")
            
            return jsonify({
                'success': True,
                'message': 'Pro status revoked successfully'
            })
        else:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'User not found or already inactive',
                'error_code': 'USER_NOT_FOUND'
            }), 404
            
    except Exception as e:
        print(f"Revoke error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint not found',
        'error_code': 'NOT_FOUND'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'message': 'Method not allowed',
        'error_code': 'METHOD_NOT_ALLOWED'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error',
        'error_code': 'INTERNAL_ERROR'
    }), 500

@app.route('/admin/statistics')
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
        daily_trends = stats.get_daily_activation_trend(days=30)
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

@app.route('/api/debug/table-info', methods=['GET', 'POST'])
def debug_table_info():
    """调试端点：获取数据库表结构信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        table_info = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            table_info[table_name] = [
                {
                    'name': col[1],
                    'type': col[2],
                    'not_null': bool(col[3]),
                    'default_value': col[4],
                    'primary_key': bool(col[5])
                }
                for col in columns
            ]
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'tables': table_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    print("🚀 启动 MoziBang 激活码验证API (SQLite版本)")
    print(f"📁 数据库文件: {DB_PATH}")
    
    # 初始化数据库
    init_database()
    
# 管理后台路由
@app.route('/admin')
def admin_redirect():
    """重定向到管理员登录页面"""
    return redirect(url_for('admin_login'))

@app.route('/')
def index():
    """根路径重定向到管理员登录页面"""
    return redirect(url_for('admin_login'))

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
        cursor.execute("SELECT COUNT(*) FROM users WHERE pro_status = 'active'")
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
                pro_status,
                COUNT(*) as total,
                SUM(CASE WHEN pro_status = 'active' THEN 1 ELSE 0 END) as active
            FROM users 
            GROUP BY pro_status
        """)
        user_stats = cursor.fetchall()
        
        # 最近激活记录
        cursor.execute("""
            SELECT email, pro_status, pro_activated_at 
            FROM users 
            WHERE pro_activated_at IS NOT NULL
            ORDER BY pro_activated_at DESC 
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

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理员登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in ADMIN_USERS and ADMIN_USERS[username] == password:
            session['admin_user'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            error = "用户名或密码错误"
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>管理员登录</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }}
                    .login-form {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 300px; }}
                    .form-group {{ margin: 20px 0; }}
                    label {{ display: block; margin-bottom: 5px; }}
                    input {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }}
                    button {{ width: 100%; padding: 12px; background: #007cba; color: white; border: none; border-radius: 4px; cursor: pointer; }}
                    button:hover {{ background: #005a8b; }}
                    .error {{ color: red; margin: 10px 0; }}
                </style>
            </head>
            <body>
                <div class="login-form">
                    <h2>MoziBang 管理后台</h2>
                    <div class="error">{error}</div>
                    <form method="post">
                        <div class="form-group">
                            <label>用户名:</label>
                            <input type="text" name="username" required>
                        </div>
                        <div class="form-group">
                            <label>密码:</label>
                            <input type="password" name="password" required>
                        </div>
                        <button type="submit">登录</button>
                    </form>
                </div>
            </body>
            </html>
            """
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>管理员登录</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }
            .login-form { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 300px; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 5px; }
            input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #007cba; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #005a8b; }
        </style>
    </head>
    <body>
        <div class="login-form">
            <h2>MoziBang 管理后台</h2>
            <form method="post">
                <div class="form-group">
                    <label>用户名:</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>密码:</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit">登录</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.route('/admin/logout')
def admin_logout():
    """管理员登出"""
    session.pop('admin_user', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/codes')
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

@app.route('/admin/users')
@login_required
def users():
    """用户管理"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = 20
        pro_type = request.args.get('pro_type', '')
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
        
        return render_template('users_list.html', 
                             users=users,
                             page=page,
                             total_pages=total_pages,
                             total=total,
                             pro_type=pro_type,
                             status=status)
    except Exception as e:
        flash(f'获取用户列表失败: {str(e)}', 'error')
        return render_template('users_list.html', users=[])

@app.route('/admin/generate', methods=['GET', 'POST'])
@login_required
def admin_generate():
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

if __name__ == '__main__':
    # 初始化数据库
    init_database()
    
    # 自动创建缺失的表（特别是pro_users表）
    try:
        from auto_create_pro_users import create_pro_users_table
        create_pro_users_table()
    except Exception as e:
        print(f"⚠️ 自动创建表时出现警告: {e}")
    
    # 根据环境配置端口和调试模式
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    if debug:
        print("🔌 API地址: http://localhost:5001/api")
        print(f"🔑 API密钥: {API_SECRET_KEY}")
        print("\n📋 可用的API端点:")
        print("  GET  /api/health - 健康检查")
        print("  POST /api/activate - 激活码验证")
        print("  POST /api/verify_pro - 验证Pro状态")
        print("  GET  /api/stats - 获取统计信息")
        print("  POST /api/revoke_pro - 撤销Pro状态")
        print("\n🔧 管理后台:")
        print("  GET  /admin - 管理仪表板")
        print("  GET  /admin/login - 管理员登录")
    else:
        print("🌐 生产环境模式")
    
    app.run(host='0.0.0.0', port=port, debug=debug)