#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端数据库pro_users表创建脚本
用于在云端环境中创建缺失的pro_users表
"""
import sqlite3
import os

def create_pro_users_table():
    """在云端数据库中创建pro_users表"""
    try:
        # 云端数据库路径
        db_path = os.path.join(os.path.dirname(__file__), 'mozibang_activation.db')
        
        print(f"连接数据库: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pro_users'")
        existing_table = cursor.fetchone()
        
        if existing_table:
            print("✅ pro_users表已存在，无需创建")
            return True
            
        print("正在创建pro_users表...")
        
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
        
        conn.commit()
        print("✅ pro_users表创建成功!")
        
        # 验证表是否创建成功
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pro_users'")
        result = cursor.fetchone()
        if result:
            print("✅ 验证成功: pro_users表已存在")
            
            # 显示表结构
            cursor.execute("PRAGMA table_info(pro_users)")
            columns = cursor.fetchall()
            print("\n📋 pro_users表结构:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
                
            return True
        else:
            print("❌ 验证失败: pro_users表未找到")
            return False
            
    except Exception as e:
        print(f"❌ 创建pro_users表失败: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def check_all_tables():
    """检查数据库中的所有表"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'mozibang_activation.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("📊 数据库中的所有表:")
        for table in tables:
            print(f"  - {table[0]}")
            
        conn.close()
        return [table[0] for table in tables]
        
    except Exception as e:
        print(f"❌ 检查表失败: {e}")
        return []

if __name__ == "__main__":
    print("🔍 检查云端数据库结构...")
    tables = check_all_tables()
    
    if 'pro_users' not in tables:
        print("\n⚠️  pro_users表不存在，开始创建...")
        success = create_pro_users_table()
        if success:
            print("\n🎉 pro_users表创建完成!")
        else:
            print("\n❌ pro_users表创建失败!")
    else:
        print("\n✅ pro_users表已存在")