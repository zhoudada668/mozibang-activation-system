#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端数据库修复脚本
直接在云端环境中运行，修复缺失的数据库表
"""

import sqlite3
import os
import sys
from datetime import datetime

# SQLite数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'mozibang_activation.db')

def check_and_create_pro_users_table():
    """检查并创建 pro_users 表"""
    try:
        print(f"正在连接数据库: {DB_PATH}")
        
        # 连接SQLite数据库
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        
        print("正在检查 pro_users 表...")
        
        # 检查表是否存在
        cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='pro_users'
        """)
        
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ pro_users 表已存在")
            # 检查记录数
            cursor.execute("SELECT COUNT(*) FROM pro_users")
            count = cursor.fetchone()[0]
            print(f"✅ pro_users 表记录数: {count}")
            return True
        
        print("❌ pro_users 表不存在，正在创建...")
        
        # 创建 pro_users 表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pro_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            pro_type TEXT NOT NULL CHECK (pro_type IN ('pro_lifetime', 'pro_1year', 'pro_6month')),
            activation_code TEXT NOT NULL,
            activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NULL DEFAULT NULL,
            last_login TIMESTAMP NULL DEFAULT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 创建索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_pro_users_email ON pro_users(email)
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

def check_all_tables():
    """检查所有表的状态"""
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        
        print("\n=== 数据库表状态检查 ===")
        
        # 获取所有表
        cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """)
        
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ 没有找到任何用户表")
            return False
        
        print(f"找到 {len(tables)} 个表:")
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} 条记录")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查表状态失败: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def main():
    """主函数"""
    print("=== MoziBang 云端数据库修复工具 ===")
    print(f"时间: {datetime.now().isoformat()}")
    print(f"数据库路径: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return False
    
    # 检查所有表状态
    check_all_tables()
    
    # 修复 pro_users 表
    success = check_and_create_pro_users_table()
    
    if success:
        print("\n🎉 数据库修复完成！")
        # 再次检查状态
        check_all_tables()
        return True
    else:
        print("\n❌ 数据库修复失败！")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)