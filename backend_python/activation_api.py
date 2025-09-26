#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MoziBang 激活码验证API
提供激活码验证、用户Pro状态管理等API接口
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import hashlib
import json
import datetime
import uuid
import logging
from functools import wraps

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # 空密码，根据实际情况修改
    'database': 'mozibang_activation',
    'charset': 'utf8mb4'
}

# API密钥配置（用于验证请求来源）
API_SECRET_KEY = "mozibang_api_secret_2024"  # 生产环境请使用更安全的密钥

def get_db_connection():
    """获取数据库连接"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None

def verify_api_key(f):
    """验证API密钥的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_SECRET_KEY:
            return jsonify({
                'success': False,
                'error': 'Invalid API key',
                'code': 'INVALID_API_KEY'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def generate_user_token(user_email):
    """生成用户访问令牌"""
    timestamp = str(datetime.datetime.now().timestamp())
    token_data = f"{user_email}:{timestamp}:{API_SECRET_KEY}"
    return hashlib.sha256(token_data.encode()).hexdigest()

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'success': True,
        'message': 'MoziBang Activation API is running',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/activate', methods=['POST'])
@verify_api_key
def activate_code():
    """激活码验证和激活接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON data',
                'code': 'INVALID_DATA'
            }), 400
        
        activation_code = data.get('activation_code', '').strip()
        user_email = data.get('user_email', '').strip()
        user_name = data.get('user_name', '').strip()
        
        if not activation_code or not user_email:
            return jsonify({
                'success': False,
                'error': 'Activation code and user email are required',
                'code': 'MISSING_REQUIRED_FIELDS'
            }), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'code': 'DB_CONNECTION_ERROR'
            }), 500
        
        try:
            with connection.cursor() as cursor:
                # 检查激活码是否存在且有效
                cursor.execute("""
                    SELECT id, code_type, expires_at, is_used, used_by, used_at, batch_id
                    FROM activation_codes 
                    WHERE code = %s AND is_active = 1
                """, (activation_code,))
                
                code_info = cursor.fetchone()
                
                if not code_info:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid activation code',
                        'code': 'INVALID_CODE'
                    }), 400
                
                code_id, code_type, expires_at, is_used, used_by, used_at, batch_id = code_info
                
                # 检查激活码是否已被使用
                if is_used:
                    return jsonify({
                        'success': False,
                        'error': 'Activation code has already been used',
                        'code': 'CODE_ALREADY_USED',
                        'used_by': used_by,
                        'used_at': used_at.isoformat() if used_at else None
                    }), 400
                
                # 检查激活码是否过期
                if expires_at and expires_at < datetime.datetime.now():
                    return jsonify({
                        'success': False,
                        'error': 'Activation code has expired',
                        'code': 'CODE_EXPIRED',
                        'expired_at': expires_at.isoformat()
                    }), 400
                
                # 检查用户是否已经是Pro用户
                cursor.execute("""
                    SELECT id, pro_type, expires_at, is_pro
                    FROM user_pro_status 
                    WHERE user_email = %s
                """, (user_email,))
                
                existing_user = cursor.fetchone()
                
                # 计算新的Pro到期时间
                now = datetime.datetime.now()
                if code_type == 'lifetime':
                    new_expires_at = None  # 永久有效
                elif code_type == '1year':
                    # 如果用户已有Pro且未过期，从现有到期时间开始计算
                    if existing_user and existing_user[2] and existing_user[2] > now:
                        new_expires_at = existing_user[2] + datetime.timedelta(days=365)
                    else:
                        new_expires_at = now + datetime.timedelta(days=365)
                elif code_type == '6month':
                    if existing_user and existing_user[2] and existing_user[2] > now:
                        new_expires_at = existing_user[2] + datetime.timedelta(days=180)
                    else:
                        new_expires_at = now + datetime.timedelta(days=180)
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid code type',
                        'code': 'INVALID_CODE_TYPE'
                    }), 400
                
                # 更新或插入用户Pro状态
                if existing_user:
                    cursor.execute("""
                        UPDATE user_pro_status 
                        SET pro_type = %s, expires_at = %s, is_pro = 1, 
                            activated_at = %s, activation_code_used = %s,
                            updated_at = %s
                        WHERE user_email = %s
                    """, (code_type, new_expires_at, now, activation_code, now, user_email))
                else:
                    cursor.execute("""
                        INSERT INTO user_pro_status 
                        (user_email, user_name, pro_type, expires_at, is_pro, 
                         activated_at, activation_code_used, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, 1, %s, %s, %s, %s)
                    """, (user_email, user_name, code_type, new_expires_at, 
                          now, activation_code, now, now))
                
                # 标记激活码为已使用
                cursor.execute("""
                    UPDATE activation_codes 
                    SET is_used = 1, used_by = %s, used_at = %s, updated_at = %s
                    WHERE id = %s
                """, (user_email, now, now, code_id))
                
                # 记录激活日志
                cursor.execute("""
                    INSERT INTO activation_logs 
                    (activation_code_id, user_email, user_name, action_type, 
                     ip_address, user_agent, created_at)
                    VALUES (%s, %s, %s, 'activate', %s, %s, %s)
                """, (code_id, user_email, user_name, 
                      request.remote_addr, request.headers.get('User-Agent', ''), now))
                
                connection.commit()
                
                # 生成用户访问令牌
                user_token = generate_user_token(user_email)
                
                return jsonify({
                    'success': True,
                    'message': 'Activation successful',
                    'data': {
                        'user_email': user_email,
                        'user_name': user_name,
                        'pro_type': code_type,
                        'expires_at': new_expires_at.isoformat() if new_expires_at else None,
                        'is_lifetime': code_type == 'lifetime',
                        'activated_at': now.isoformat(),
                        'user_token': user_token
                    }
                })
                
        except Exception as e:
            connection.rollback()
            logger.error(f"激活过程中发生错误: {e}")
            return jsonify({
                'success': False,
                'error': 'Activation failed',
                'code': 'ACTIVATION_ERROR'
            }), 500
        
        finally:
            connection.close()
            
    except Exception as e:
        logger.error(f"激活接口错误: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/verify-pro', methods=['POST'])
@verify_api_key
def verify_pro_status():
    """验证用户Pro状态接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON data',
                'code': 'INVALID_DATA'
            }), 400
        
        user_email = data.get('user_email', '').strip()
        
        if not user_email:
            return jsonify({
                'success': False,
                'error': 'User email is required',
                'code': 'MISSING_EMAIL'
            }), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'code': 'DB_CONNECTION_ERROR'
            }), 500
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT user_email, user_name, pro_type, expires_at, is_pro, 
                           activated_at, activation_code_used, last_login
                    FROM user_pro_status 
                    WHERE user_email = %s
                """, (user_email,))
                
                user_info = cursor.fetchone()
                
                if not user_info:
                    return jsonify({
                        'success': True,
                        'data': {
                            'user_email': user_email,
                            'is_pro': False,
                            'pro_type': None,
                            'expires_at': None,
                            'is_expired': False
                        }
                    })
                
                user_email, user_name, pro_type, expires_at, is_pro, activated_at, activation_code_used, last_login = user_info
                
                # 检查是否过期
                is_expired = False
                if expires_at and expires_at < datetime.datetime.now():
                    is_expired = True
                    is_pro = False
                
                # 更新最后登录时间
                cursor.execute("""
                    UPDATE user_pro_status 
                    SET last_login = %s 
                    WHERE user_email = %s
                """, (datetime.datetime.now(), user_email))
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'data': {
                        'user_email': user_email,
                        'user_name': user_name,
                        'is_pro': is_pro and not is_expired,
                        'pro_type': pro_type,
                        'expires_at': expires_at.isoformat() if expires_at else None,
                        'is_expired': is_expired,
                        'is_lifetime': pro_type == 'lifetime',
                        'activated_at': activated_at.isoformat() if activated_at else None,
                        'activation_code_used': activation_code_used,
                        'last_login': last_login.isoformat() if last_login else None
                    }
                })
                
        finally:
            connection.close()
            
    except Exception as e:
        logger.error(f"验证Pro状态错误: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/user-stats', methods=['GET'])
@verify_api_key
def get_user_stats():
    """获取用户统计信息接口"""
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'code': 'DB_CONNECTION_ERROR'
            }), 500
        
        try:
            with connection.cursor() as cursor:
                # 获取各种统计数据
                stats = {}
                
                # Pro用户总数
                cursor.execute("SELECT COUNT(*) FROM user_pro_status WHERE is_pro = 1")
                stats['total_pro_users'] = cursor.fetchone()[0]
                
                # 各类型Pro用户数量
                cursor.execute("""
                    SELECT pro_type, COUNT(*) 
                    FROM user_pro_status 
                    WHERE is_pro = 1 
                    GROUP BY pro_type
                """)
                pro_type_stats = dict(cursor.fetchall())
                stats['pro_type_distribution'] = pro_type_stats
                
                # 今日新增Pro用户
                today = datetime.date.today()
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM user_pro_status 
                    WHERE DATE(activated_at) = %s
                """, (today,))
                stats['today_new_users'] = cursor.fetchone()[0]
                
                # 本月新增Pro用户
                first_day_of_month = today.replace(day=1)
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM user_pro_status 
                    WHERE activated_at >= %s
                """, (first_day_of_month,))
                stats['month_new_users'] = cursor.fetchone()[0]
                
                # 过期用户数量
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM user_pro_status 
                    WHERE expires_at IS NOT NULL AND expires_at < NOW()
                """)
                stats['expired_users'] = cursor.fetchone()[0]
                
                return jsonify({
                    'success': True,
                    'data': stats
                })
                
        finally:
            connection.close()
            
    except Exception as e:
        logger.error(f"获取用户统计错误: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/revoke-pro', methods=['POST'])
@verify_api_key
def revoke_pro_status():
    """撤销用户Pro状态接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON data',
                'code': 'INVALID_DATA'
            }), 400
        
        user_email = data.get('user_email', '').strip()
        reason = data.get('reason', '').strip()
        
        if not user_email:
            return jsonify({
                'success': False,
                'error': 'User email is required',
                'code': 'MISSING_EMAIL'
            }), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'code': 'DB_CONNECTION_ERROR'
            }), 500
        
        try:
            with connection.cursor() as cursor:
                # 检查用户是否存在
                cursor.execute("""
                    SELECT id, activation_code_used 
                    FROM user_pro_status 
                    WHERE user_email = %s AND is_pro = 1
                """, (user_email,))
                
                user_info = cursor.fetchone()
                
                if not user_info:
                    return jsonify({
                        'success': False,
                        'error': 'User not found or not a Pro user',
                        'code': 'USER_NOT_FOUND'
                    }), 404
                
                user_id, activation_code_used = user_info
                
                # 撤销Pro状态
                cursor.execute("""
                    UPDATE user_pro_status 
                    SET is_pro = 0, updated_at = %s
                    WHERE user_email = %s
                """, (datetime.datetime.now(), user_email))
                
                # 记录撤销日志
                if activation_code_used:
                    cursor.execute("""
                        SELECT id FROM activation_codes WHERE code = %s
                    """, (activation_code_used,))
                    code_result = cursor.fetchone()
                    code_id = code_result[0] if code_result else None
                    
                    cursor.execute("""
                        INSERT INTO activation_logs 
                        (activation_code_id, user_email, action_type, 
                         ip_address, user_agent, notes, created_at)
                        VALUES (%s, %s, 'revoke', %s, %s, %s, %s)
                    """, (code_id, user_email, request.remote_addr, 
                          request.headers.get('User-Agent', ''), reason, datetime.datetime.now()))
                
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Pro status revoked successfully',
                    'data': {
                        'user_email': user_email,
                        'revoked_at': datetime.datetime.now().isoformat(),
                        'reason': reason
                    }
                })
                
        finally:
            connection.close()
            
    except Exception as e:
        logger.error(f"撤销Pro状态错误: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

if __name__ == '__main__':
    print("MoziBang 激活码验证API启动中...")
    print("API接口列表:")
    print("  GET  /api/health        - 健康检查")
    print("  POST /api/activate      - 激活码验证和激活")
    print("  POST /api/verify-pro    - 验证用户Pro状态")
    print("  GET  /api/user-stats    - 获取用户统计信息")
    print("  POST /api/revoke-pro    - 撤销用户Pro状态")
    print("\n请确保:")
    print("1. 数据库配置正确")
    print("2. 数据库表已创建")
    print("3. API密钥已配置")
    print("\n启动服务器...")
    
    app.run(host='0.0.0.0', port=5001, debug=True)