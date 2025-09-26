#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MoziBang 激活码系统 - SQLite数据库初始化脚本
使用SQLite数据库，无需额外配置
"""

import sqlite3
import hashlib
import secrets
import sys
from datetime import datetime, timedelta
import os

# SQLite数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'mozibang_activation.db')

def generate_password_hash(password):
    """生成密码哈希"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"pbkdf2:sha256:100000${salt}${password_hash.hex()}"

def create_database_and_tables():
    """创建数据库和表"""
    try:
        # 连接SQLite数据库
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        
        print("正在创建数据库表结构...")
        
        # 1. 激活码表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS activation_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            code_type TEXT NOT NULL CHECK (code_type IN ('pro_lifetime', 'pro_1year', 'pro_6month')),
            batch_name TEXT DEFAULT NULL,
            notes TEXT DEFAULT NULL,
            is_used BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used_at TIMESTAMP NULL DEFAULT NULL,
            used_by_email TEXT DEFAULT NULL,
            used_by_name TEXT DEFAULT NULL,
            expires_at TIMESTAMP NULL DEFAULT NULL,
            is_disabled BOOLEAN DEFAULT FALSE,
            disabled_at TIMESTAMP NULL DEFAULT NULL,
            disabled_reason TEXT DEFAULT NULL
        )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_code ON activation_codes(code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_code_type ON activation_codes(code_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_used ON activation_codes(is_used)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_used_by_email ON activation_codes(used_by_email)")
        
        # 2. Pro用户表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pro_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL UNIQUE,
            user_name TEXT DEFAULT NULL,
            pro_type TEXT NOT NULL CHECK (pro_type IN ('pro_lifetime', 'pro_1year', 'pro_6month')),
            activation_code TEXT NOT NULL,
            activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NULL DEFAULT NULL,
            is_lifetime BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            last_login TIMESTAMP NULL DEFAULT NULL,
            user_token TEXT DEFAULT NULL,
            revoked_at TIMESTAMP NULL DEFAULT NULL,
            revoked_reason TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_email ON pro_users(user_email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pro_type ON pro_users(pro_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON pro_users(is_active)")
        
        # 3. 管理员表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            email TEXT DEFAULT NULL,
            full_name TEXT DEFAULT NULL,
            role TEXT DEFAULT 'admin' CHECK (role IN ('super_admin', 'admin', 'operator')),
            is_active BOOLEAN DEFAULT TRUE,
            last_login TIMESTAMP NULL DEFAULT NULL,
            login_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 4. 操作日志表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER DEFAULT NULL,
            admin_username TEXT DEFAULT NULL,
            operation_type TEXT NOT NULL CHECK (operation_type IN ('login', 'logout', 'generate_codes', 'disable_code', 'revoke_user', 'view_stats', 'export_data')),
            operation_desc TEXT DEFAULT NULL,
            target_type TEXT DEFAULT NULL CHECK (target_type IN ('activation_code', 'pro_user', 'admin_user', 'system')),
            target_id TEXT DEFAULT NULL,
            ip_address TEXT DEFAULT NULL,
            user_agent TEXT DEFAULT NULL,
            operation_result TEXT DEFAULT 'success' CHECK (operation_result IN ('success', 'failure', 'partial')),
            error_message TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 5. 系统配置表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT NOT NULL UNIQUE,
            config_value TEXT DEFAULT NULL,
            config_type TEXT DEFAULT 'string' CHECK (config_type IN ('string', 'number', 'boolean', 'json')),
            description TEXT DEFAULT NULL,
            is_public BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        print("正在插入初始数据...")
        
        # 插入默认管理员账号
        admin_password_hash = generate_password_hash('admin123')
        cursor.execute("""
        INSERT OR REPLACE INTO admin_users (username, password_hash, email, full_name, role, is_active) 
        VALUES (?, ?, ?, ?, ?, ?)
        """, ('admin', admin_password_hash, 'admin@mozibang.com', '系统管理员', 'super_admin', True))
        
        # 插入系统配置
        configs = [
            ('system_name', 'MoziBang激活码系统', 'string', '系统名称', True),
            ('version', '1.0.0', 'string', '系统版本', True),
            ('max_codes_per_batch', '1000', 'number', '每批次最大激活码数量', False),
            ('code_length', '16', 'number', '激活码长度', False),
            ('api_timeout', '30', 'number', 'API超时时间(秒)', False),
            ('enable_email_notification', 'false', 'boolean', '是否启用邮件通知', False),
            ('maintenance_mode', 'false', 'boolean', '维护模式', False)
        ]
        
        for config in configs:
            cursor.execute("""
            INSERT OR REPLACE INTO system_config (config_key, config_value, config_type, description, is_public) 
            VALUES (?, ?, ?, ?, ?)
            """, config)
        
        # 生成示例激活码
        print("正在生成示例激活码...")
        sample_codes = [
            ('DEMO-LIFE-TIME-0001', 'pro_lifetime', '演示批次', '永久版本演示激活码'),
            ('DEMO-1YR-CODE-0001', 'pro_1year', '演示批次', '1年版本演示激活码'),
            ('DEMO-6M-CODE-0001', 'pro_6month', '演示批次', '6个月版本演示激活码'),
        ]
        
        for code, code_type, batch, notes in sample_codes:
            cursor.execute("""
            INSERT OR REPLACE INTO activation_codes (code, code_type, batch_name, notes)
            VALUES (?, ?, ?, ?)
            """, (code, code_type, batch, notes))
        
        connection.commit()
        
        print("✅ SQLite数据库初始化完成！")
        print(f"\n📁 数据库文件位置: {DB_PATH}")
        
        print("\n📊 创建的表:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        print("\n👤 默认管理员账号:")
        print("  用户名: admin")
        print("  密码: admin123")
        print("  角色: super_admin")
        
        print("\n🎫 可用的演示激活码:")
        for code, code_type, batch, notes in sample_codes:
            print(f"  - {code} ({code_type})")
        
        print("\n🌐 管理后台地址:")
        print("  http://localhost:5000")
        
        print("\n🔌 API接口地址:")
        print("  http://localhost:5001/api")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False
        
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    print("🚀 MoziBang 激活码系统 - SQLite数据库初始化")
    print("=" * 50)
    
    print(f"数据库文件: {DB_PATH}")
    
    # 自动初始化
    if create_database_and_tables():
        print("\n🎉 初始化完成！现在可以启动管理后台和API服务了。")
        print("\n📝 注意: 请更新后端配置文件以使用SQLite数据库")
    else:
        print("\n❌ 初始化失败。")
        sys.exit(1)