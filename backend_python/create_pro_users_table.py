#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import os

def create_pro_users_table():
    """创建pro_users表"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'mozibang_activation.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
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
        else:
            print("❌ 验证失败: pro_users表未找到")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ 创建pro_users表失败: {e}")

if __name__ == "__main__":
    create_pro_users_table()