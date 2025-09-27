#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端数据库同步脚本
确保云端环境有完整的数据库结构，特别是pro_users表
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

def check_and_create_pro_users_table():
    """检查并创建pro_users表"""
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        
        print("🔍 检查pro_users表是否存在...")
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pro_users'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ pro_users表已存在")
            
            # 检查表结构
            cursor.execute("PRAGMA table_info(pro_users)")
            columns = cursor.fetchall()
            print(f"📋 表结构 ({len(columns)} 列):")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
                
            return True
        
        print("⚠️  pro_users表不存在，正在创建...")
        
        # 创建pro_users表
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
        
        connection.commit()
        print("✅ pro_users表创建成功!")
        
        # 验证创建结果
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pro_users'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(pro_users)")
            columns = cursor.fetchall()
            print(f"📋 新建表结构 ({len(columns)} 列):")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            return True
        else:
            print("❌ 表创建验证失败")
            return False
            
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        return False
        
    finally:
        if connection:
            connection.close()

def sync_all_tables():
    """同步所有必要的表结构"""
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        
        print("🔄 开始同步数据库表结构...")
        
        # 1. 激活码表
        print("📝 检查activation_codes表...")
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
        
        # 2. Pro用户表
        print("📝 检查pro_users表...")
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
        
        # 3. 管理员表
        print("📝 检查admin_users表...")
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
        
        # 创建所有索引
        print("📝 创建索引...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_code ON activation_codes(code)",
            "CREATE INDEX IF NOT EXISTS idx_code_type ON activation_codes(code_type)",
            "CREATE INDEX IF NOT EXISTS idx_is_used ON activation_codes(is_used)",
            "CREATE INDEX IF NOT EXISTS idx_user_email ON pro_users(user_email)",
            "CREATE INDEX IF NOT EXISTS idx_pro_type ON pro_users(pro_type)",
            "CREATE INDEX IF NOT EXISTS idx_is_active ON pro_users(is_active)",
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        # 确保有默认管理员
        cursor.execute("SELECT COUNT(*) FROM admin_users WHERE username = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            print("📝 创建默认管理员账号...")
            admin_password_hash = generate_password_hash('admin123')
            cursor.execute("""
            INSERT INTO admin_users (username, password_hash, email, full_name, role, is_active) 
            VALUES (?, ?, ?, ?, ?, ?)
            """, ('admin', admin_password_hash, 'admin@mozibang.com', '系统管理员', 'super_admin', True))
        
        connection.commit()
        
        # 显示最终状态
        print("\n📊 数据库表列表:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]} ({count} 条记录)")
        
        print("✅ 数据库同步完成!")
        return True
        
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        return False
        
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    print("🚀 云端数据库同步工具")
    print("=" * 40)
    print(f"📁 数据库文件: {DB_PATH}")
    
    # 检查数据库文件是否存在
    if not os.path.exists(DB_PATH):
        print("⚠️  数据库文件不存在，将创建新的数据库")
    
    # 执行同步
    if sync_all_tables():
        print("\n🎉 同步成功! 云端数据库已准备就绪")
        
        # 特别检查pro_users表
        if check_and_create_pro_users_table():
            print("✅ pro_users表状态正常")
        else:
            print("❌ pro_users表存在问题")
            
    else:
        print("\n❌ 同步失败")
        sys.exit(1)