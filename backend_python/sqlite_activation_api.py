#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MoziBang 激活码验证API - SQLite版本
提供激活码验证、Pro状态管理等功能
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hashlib
import secrets
import string
from datetime import datetime, timedelta
import os
from functools import wraps

app = Flask(__name__)

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
    return hashlib.sha256(f"{user_email}_{datetime.datetime.now().isoformat()}".encode()).hexdigest()

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'sqlite',
        'database_file': DB_PATH
    })

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
        cursor.execute("SELECT * FROM pro_users WHERE user_email = ?", (user_email,))
        existing_user = cursor.fetchone()
        
        if existing_user and existing_user['is_active']:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'User already has active Pro status',
                'error_code': 'ALREADY_PRO_USER'
            }), 400
        
        # 计算过期时间
        expires_at = None
        is_lifetime = False
        
        if code_record['code_type'] == 'pro_lifetime':
            is_lifetime = True
        elif code_record['code_type'] == 'pro_1year':
            expires_at = (datetime.datetime.now() + datetime.timedelta(days=365)).isoformat()
        elif code_record['code_type'] == 'pro_6month':
            expires_at = (datetime.datetime.now() + datetime.timedelta(days=180)).isoformat()
        
        # 生成用户令牌
        user_token = generate_user_token(user_email)
        
        # 开始事务
        try:
            # 标记激活码为已使用
            cursor.execute("""
                UPDATE activation_codes 
                SET is_used = 1, used_at = CURRENT_TIMESTAMP, used_by_email = ?, used_by_name = ?
                WHERE code = ?
            """, (user_email, user_name, activation_code))
            
            # 添加或更新Pro用户记录
            if existing_user:
                cursor.execute("""
                    UPDATE pro_users 
                    SET pro_type = ?, activation_code = ?, activated_at = CURRENT_TIMESTAMP,
                        expires_at = ?, is_lifetime = ?, is_active = 1, user_token = ?,
                        revoked_at = NULL, revoked_reason = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE user_email = ?
                """, (code_record['code_type'], activation_code, expires_at, is_lifetime, user_token, user_email))
            else:
                cursor.execute("""
                    INSERT INTO pro_users 
                    (user_email, user_name, pro_type, activation_code, expires_at, is_lifetime, user_token)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_email, user_name, code_record['code_type'], activation_code, expires_at, is_lifetime, user_token))
            
            conn.commit()
            
            logger.info(f"Activation successful: {user_email} -> {activation_code}")
            
            return jsonify({
                'success': True,
                'message': 'Activation successful',
                'data': {
                    'user_email': user_email,
                    'pro_type': code_record['code_type'],
                    'is_lifetime': is_lifetime,
                    'expires_at': expires_at,
                    'user_token': user_token,
                    'activated_at': datetime.datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            conn.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"Activation error: {str(e)}")
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
            SELECT * FROM pro_users 
            WHERE user_email = ? AND is_active = 1
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
        if not user_record['is_lifetime'] and user_record['expires_at']:
            expires_at = datetime.datetime.fromisoformat(user_record['expires_at'])
            if expires_at < datetime.datetime.now():
                is_expired = True
        
        # 更新最后登录时间
        cursor.execute("""
            UPDATE pro_users 
            SET last_login = CURRENT_TIMESTAMP 
            WHERE user_email = ?
        """, (user_email,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Pro status verified',
            'data': {
                'is_pro': not is_expired,
                'pro_type': user_record['pro_type'],
                'is_lifetime': bool(user_record['is_lifetime']),
                'expires_at': user_record['expires_at'],
                'activated_at': user_record['activated_at'],
                'is_expired': is_expired,
                'last_login': datetime.datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Pro status verification error: {str(e)}")
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
                code_type,
                COUNT(*) as total,
                SUM(CASE WHEN is_used = 1 THEN 1 ELSE 0 END) as used,
                SUM(CASE WHEN is_used = 0 AND is_disabled = 0 THEN 1 ELSE 0 END) as available,
                SUM(CASE WHEN is_disabled = 1 THEN 1 ELSE 0 END) as disabled
            FROM activation_codes 
            GROUP BY code_type
        """)
        code_stats = [dict(row) for row in cursor.fetchall()]
        
        # Pro用户统计
        cursor.execute("""
            SELECT 
                pro_type,
                COUNT(*) as total,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive
            FROM pro_users 
            GROUP BY pro_type
        """)
        user_stats = [dict(row) for row in cursor.fetchall()]
        
        # 总体统计
        cursor.execute("SELECT COUNT(*) as total FROM activation_codes")
        total_codes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as total FROM pro_users WHERE is_active = 1")
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
        logger.error(f"Stats error: {str(e)}")
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
            UPDATE pro_users 
            SET is_active = 0, revoked_at = CURRENT_TIMESTAMP, revoked_reason = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_email = ? AND is_active = 1
        """, (reason, user_email))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            
            logger.info(f"Pro status revoked: {user_email}")
            
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
        logger.error(f"Revoke error: {str(e)}")
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

if __name__ == '__main__':
    print("🚀 启动 MoziBang 激活码验证API (SQLite版本)")
    print(f"📁 数据库文件: {DB_PATH}")
    
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
    else:
        print("🌐 生产环境模式")
    
    app.run(host='0.0.0.0', port=port, debug=debug)