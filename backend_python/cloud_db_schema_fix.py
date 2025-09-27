#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端数据库字段修复脚本
修复pro_users表的字段名不一致问题
确保使用user_email而不是email字段
"""

import sqlite3
import os
import sys
from datetime import datetime

# SQLite数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'mozibang_activation.db')

def check_pro_users_schema():
    """检查pro_users表的字段结构"""
    try:
        print(f"正在检查数据库: {DB_PATH}")
        
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        
        # 检查表是否存在
        cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='pro_users'
        """)
        
        if not cursor.fetchone():
            print("❌ pro_users表不存在")
            return False
        
        # 获取表结构
        cursor.execute("PRAGMA table_info(pro_users)")
        columns = cursor.fetchall()
        
        print("当前pro_users表结构:")
        column_names = []
        for col in columns:
            column_names.append(col[1])
            print(f"  - {col[1]} ({col[2]})")
        
        # 检查是否有user_email字段
        has_user_email = 'user_email' in column_names
        has_email = 'email' in column_names
        
        print(f"\n字段检查结果:")
        print(f"  - user_email字段: {'✅ 存在' if has_user_email else '❌ 不存在'}")
        print(f"  - email字段: {'✅ 存在' if has_email else '❌ 不存在'}")
        
        return has_user_email, has_email, column_names
        
    except Exception as e:
        print(f"❌ 检查表结构失败: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def fix_pro_users_schema():
    """修复pro_users表的字段结构"""
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        
        # 检查当前表结构
        result = check_pro_users_schema()
        if not result:
            return False
            
        has_user_email, has_email, column_names = result
        
        if has_user_email:
            print("✅ user_email字段已存在，无需修复")
            return True
        
        if not has_email:
            print("❌ 既没有user_email也没有email字段，需要重新创建表")
            return create_correct_pro_users_table()
        
        print("🔧 开始修复字段名...")
        
        # 备份原表数据
        print("1. 备份原表数据...")
        cursor.execute("SELECT * FROM pro_users")
        backup_data = cursor.fetchall()
        print(f"   备份了 {len(backup_data)} 条记录")
        
        # 重命名原表
        print("2. 重命名原表...")
        cursor.execute("ALTER TABLE pro_users RENAME TO pro_users_backup")
        
        # 创建新表（使用正确的字段名）
        print("3. 创建新表...")
        cursor.execute("""
        CREATE TABLE pro_users (
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
        
        # 迁移数据
        print("4. 迁移数据...")
        if backup_data:
            # 获取备份表的字段信息
            cursor.execute("PRAGMA table_info(pro_users_backup)")
            backup_columns = [col[1] for col in cursor.fetchall()]
            
            # 构建插入语句
            insert_fields = []
            select_fields = []
            
            field_mapping = {
                'id': 'id',
                'user_email': 'email' if 'email' in backup_columns else 'user_email',
                'user_name': 'name' if 'name' in backup_columns else 'user_name',
                'pro_type': 'pro_type',
                'activation_code': 'activation_code',
                'activated_at': 'activated_at',
                'expires_at': 'expires_at',
                'is_lifetime': 'is_lifetime',
                'is_active': 'is_active',
                'last_login': 'last_login',
                'user_token': 'user_token',
                'revoked_at': 'revoked_at',
                'revoked_reason': 'revoked_reason',
                'created_at': 'created_at',
                'updated_at': 'updated_at'
            }
            
            for new_field, old_field in field_mapping.items():
                if old_field in backup_columns:
                    insert_fields.append(new_field)
                    select_fields.append(old_field)
            
            insert_sql = f"""
            INSERT INTO pro_users ({', '.join(insert_fields)})
            SELECT {', '.join(select_fields)}
            FROM pro_users_backup
            """
            
            cursor.execute(insert_sql)
            migrated_count = cursor.rowcount
            print(f"   迁移了 {migrated_count} 条记录")
        
        # 创建索引
        print("5. 创建索引...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_email ON pro_users(user_email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pro_type ON pro_users(pro_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON pro_users(is_active)")
        
        # 提交更改
        connection.commit()
        
        # 验证修复结果
        print("6. 验证修复结果...")
        cursor.execute("SELECT COUNT(*) FROM pro_users")
        final_count = cursor.fetchone()[0]
        print(f"   新表记录数: {final_count}")
        
        # 删除备份表
        print("7. 清理备份表...")
        cursor.execute("DROP TABLE pro_users_backup")
        connection.commit()
        
        print("✅ 字段修复完成!")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        # 尝试恢复
        try:
            cursor.execute("DROP TABLE IF EXISTS pro_users")
            cursor.execute("ALTER TABLE pro_users_backup RENAME TO pro_users")
            connection.commit()
            print("🔄 已恢复原表")
        except:
            pass
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def create_correct_pro_users_table():
    """创建正确的pro_users表"""
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        
        print("创建正确的pro_users表...")
        
        # 删除现有表（如果存在）
        cursor.execute("DROP TABLE IF EXISTS pro_users")
        
        # 创建新表
        cursor.execute("""
        CREATE TABLE pro_users (
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
        print("✅ 表创建成功!")
        return True
        
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def main():
    """主函数"""
    print("=== MoziBang 云端数据库字段修复工具 ===")
    print(f"时间: {datetime.now().isoformat()}")
    print(f"数据库路径: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return False
    
    # 检查并修复表结构
    success = fix_pro_users_schema()
    
    if success:
        print("\n🎉 数据库字段修复完成！")
        print("现在统计功能应该可以正常工作了。")
        return True
    else:
        print("\n❌ 数据库字段修复失败！")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)