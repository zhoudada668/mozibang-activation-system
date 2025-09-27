#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动创建 pro_users 表的脚本
用于云端部署时自动初始化缺失的数据库表
"""

import sqlite3
import os
import sys

# SQLite数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'mozibang_activation.db')

def create_pro_users_table():
    """创建 pro_users 表"""
    try:
        # 连接SQLite数据库
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        
        print("正在检查并创建 pro_users 表...")
        
        # 检查表是否存在
        cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='pro_users'
        """)
        
        if cursor.fetchone():
            print("pro_users 表已存在")
            return True
        
        # 创建 pro_users 表
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
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_pro_users_user_email ON pro_users(user_email)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_pro_users_activation_code ON pro_users(activation_code)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_pro_users_pro_type ON pro_users(pro_type)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_pro_users_is_active ON pro_users(is_active)
        """)
        
        # 提交更改
        connection.commit()
        print("✅ pro_users 表创建成功")
        
        # 验证表创建
        cursor.execute("SELECT COUNT(*) FROM pro_users")
        count = cursor.fetchone()[0]
        print(f"✅ pro_users 表验证成功，当前记录数: {count}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 数据库错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def main():
    """主函数"""
    print("=== MoziBang 激活码系统 - 自动创建 pro_users 表 ===")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return False
    
    success = create_pro_users_table()
    
    if success:
        print("🎉 pro_users 表创建完成！")
        return True
    else:
        print("❌ pro_users 表创建失败！")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)