#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MoziBang 激活码系统 - 数据库初始化脚本
"""

import pymysql
import hashlib
import secrets
import sys
from datetime import datetime

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',  # 请根据实际情况修改
    'charset': 'utf8mb4'
}

def generate_password_hash(password):
    """生成密码哈希"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"pbkdf2:sha256:100000${salt}${password_hash.hex()}"

def create_database_and_tables():
    """创建数据库和表"""
    connection = None
    try:
        # 连接MySQL服务器
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("正在创建数据库...")
        
        # 创建数据库
        cursor.execute("CREATE DATABASE IF NOT EXISTS mozibang_activation DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute("USE mozibang_activation")
        
        print("正在创建表结构...")
        
        # 1. 激活码表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS activation_codes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(32) NOT NULL UNIQUE COMMENT '激活码',
            code_type ENUM('pro_lifetime', 'pro_1year', 'pro_6month') NOT NULL COMMENT '激活码类型',
            batch_name VARCHAR(100) DEFAULT NULL COMMENT '批次名称',
            notes TEXT DEFAULT NULL COMMENT '备注信息',
            is_used BOOLEAN DEFAULT FALSE COMMENT '是否已使用',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            used_at TIMESTAMP NULL DEFAULT NULL COMMENT '使用时间',
            used_by_email VARCHAR(255) DEFAULT NULL COMMENT '使用者邮箱',
            used_by_name VARCHAR(100) DEFAULT NULL COMMENT '使用者姓名',
            expires_at TIMESTAMP NULL DEFAULT NULL COMMENT '激活码过期时间',
            is_disabled BOOLEAN DEFAULT FALSE COMMENT '是否已禁用',
            disabled_at TIMESTAMP NULL DEFAULT NULL COMMENT '禁用时间',
            disabled_reason VARCHAR(255) DEFAULT NULL COMMENT '禁用原因',
            INDEX idx_code (code),
            INDEX idx_code_type (code_type),
            INDEX idx_batch_name (batch_name),
            INDEX idx_is_used (is_used),
            INDEX idx_used_by_email (used_by_email),
            INDEX idx_created_at (created_at),
            INDEX idx_used_at (used_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='激活码表'
        """)
        
        # 2. Pro用户表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pro_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) NOT NULL UNIQUE COMMENT '用户邮箱',
            user_name VARCHAR(100) DEFAULT NULL COMMENT '用户姓名',
            pro_type ENUM('pro_lifetime', 'pro_1year', 'pro_6month') NOT NULL COMMENT 'Pro类型',
            activation_code VARCHAR(32) NOT NULL COMMENT '使用的激活码',
            activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '激活时间',
            expires_at TIMESTAMP NULL DEFAULT NULL COMMENT 'Pro到期时间',
            is_lifetime BOOLEAN DEFAULT FALSE COMMENT '是否永久有效',
            is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活状态',
            last_login TIMESTAMP NULL DEFAULT NULL COMMENT '最后登录时间',
            user_token VARCHAR(64) DEFAULT NULL COMMENT '用户令牌',
            revoked_at TIMESTAMP NULL DEFAULT NULL COMMENT '撤销时间',
            revoked_reason VARCHAR(255) DEFAULT NULL COMMENT '撤销原因',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_user_email (user_email),
            INDEX idx_pro_type (pro_type),
            INDEX idx_activation_code (activation_code),
            INDEX idx_activated_at (activated_at),
            INDEX idx_expires_at (expires_at),
            INDEX idx_is_active (is_active),
            INDEX idx_last_login (last_login)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Pro用户表'
        """)
        
        # 3. 管理员表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE COMMENT '管理员用户名',
            password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
            email VARCHAR(255) DEFAULT NULL COMMENT '管理员邮箱',
            full_name VARCHAR(100) DEFAULT NULL COMMENT '管理员姓名',
            role ENUM('super_admin', 'admin', 'operator') DEFAULT 'admin' COMMENT '角色',
            is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
            last_login TIMESTAMP NULL DEFAULT NULL COMMENT '最后登录时间',
            login_count INT DEFAULT 0 COMMENT '登录次数',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_username (username),
            INDEX idx_role (role),
            INDEX idx_is_active (is_active)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员表'
        """)
        
        # 4. 操作日志表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            admin_id INT DEFAULT NULL COMMENT '管理员ID',
            admin_username VARCHAR(50) DEFAULT NULL COMMENT '管理员用户名',
            operation_type ENUM('login', 'logout', 'generate_codes', 'disable_code', 'revoke_user', 'view_stats', 'export_data') NOT NULL COMMENT '操作类型',
            operation_desc TEXT DEFAULT NULL COMMENT '操作描述',
            target_type ENUM('activation_code', 'pro_user', 'admin_user', 'system') DEFAULT NULL COMMENT '操作目标类型',
            target_id VARCHAR(100) DEFAULT NULL COMMENT '操作目标ID',
            ip_address VARCHAR(45) DEFAULT NULL COMMENT 'IP地址',
            user_agent TEXT DEFAULT NULL COMMENT '用户代理',
            operation_result ENUM('success', 'failure', 'partial') DEFAULT 'success' COMMENT '操作结果',
            error_message TEXT DEFAULT NULL COMMENT '错误信息',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
            INDEX idx_admin_id (admin_id),
            INDEX idx_operation_type (operation_type),
            INDEX idx_target_type (target_type),
            INDEX idx_target_id (target_id),
            INDEX idx_created_at (created_at),
            INDEX idx_operation_result (operation_result)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表'
        """)
        
        # 5. 系统配置表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            id INT AUTO_INCREMENT PRIMARY KEY,
            config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
            config_value TEXT DEFAULT NULL COMMENT '配置值',
            config_type ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string' COMMENT '配置类型',
            description TEXT DEFAULT NULL COMMENT '配置描述',
            is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开配置',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_config_key (config_key),
            INDEX idx_is_public (is_public)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表'
        """)
        
        print("正在插入初始数据...")
        
        # 插入默认管理员账号
        admin_password_hash = generate_password_hash('admin123')
        cursor.execute("""
        INSERT INTO admin_users (username, password_hash, email, full_name, role, is_active) 
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
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
            INSERT INTO system_config (config_key, config_value, config_type, description, is_public) 
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
            """, config)
        
        # 创建视图
        print("正在创建视图...")
        
        # 激活码统计视图
        cursor.execute("""
        CREATE OR REPLACE VIEW v_activation_stats AS
        SELECT 
            code_type,
            COUNT(*) as total_count,
            SUM(CASE WHEN is_used = TRUE THEN 1 ELSE 0 END) as used_count,
            SUM(CASE WHEN is_used = FALSE AND is_disabled = FALSE THEN 1 ELSE 0 END) as available_count,
            SUM(CASE WHEN is_disabled = TRUE THEN 1 ELSE 0 END) as disabled_count,
            MIN(created_at) as first_created,
            MAX(created_at) as last_created
        FROM activation_codes 
        GROUP BY code_type
        """)
        
        # Pro用户统计视图
        cursor.execute("""
        CREATE OR REPLACE VIEW v_pro_user_stats AS
        SELECT 
            pro_type,
            COUNT(*) as total_count,
            SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as active_count,
            SUM(CASE WHEN is_active = FALSE THEN 1 ELSE 0 END) as inactive_count,
            SUM(CASE WHEN expires_at IS NULL OR expires_at > NOW() THEN 1 ELSE 0 END) as valid_count,
            SUM(CASE WHEN expires_at IS NOT NULL AND expires_at <= NOW() THEN 1 ELSE 0 END) as expired_count,
            MIN(activated_at) as first_activation,
            MAX(activated_at) as last_activation
        FROM pro_users 
        GROUP BY pro_type
        """)
        
        connection.commit()
        
        print("✅ 数据库初始化完成！")
        print("\n📊 创建的表:")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        print("\n👤 默认管理员账号:")
        print("  用户名: admin")
        print("  密码: admin123")
        print("  角色: super_admin")
        
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

def generate_sample_codes():
    """生成示例激活码"""
    try:
        connection = pymysql.connect(**DB_CONFIG, database='mozibang_activation')
        cursor = connection.cursor()
        
        print("\n正在生成示例激活码...")
        
        # 生成不同类型的激活码
        sample_codes = [
            ('DEMO-LIFE-TIME-0001', 'pro_lifetime', '演示批次', '永久版本演示激活码'),
            ('DEMO-1YR-CODE-0001', 'pro_1year', '演示批次', '1年版本演示激活码'),
            ('DEMO-6M-CODE-0001', 'pro_6month', '演示批次', '6个月版本演示激活码'),
        ]
        
        for code, code_type, batch, notes in sample_codes:
            cursor.execute("""
            INSERT INTO activation_codes (code, code_type, batch_name, notes)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE notes = VALUES(notes)
            """, (code, code_type, batch, notes))
        
        connection.commit()
        
        print("✅ 示例激活码生成完成！")
        print("\n🎫 可用的演示激活码:")
        for code, code_type, batch, notes in sample_codes:
            print(f"  - {code} ({code_type})")
        
        return True
        
    except Exception as e:
        print(f"❌ 生成示例激活码失败: {e}")
        return False
        
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    print("🚀 MoziBang 激活码系统 - 数据库初始化")
    print("=" * 50)
    
    # 检查数据库配置
    print(f"数据库配置:")
    print(f"  主机: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"  用户: {DB_CONFIG['user']}")
    print(f"  字符集: {DB_CONFIG['charset']}")
    
    if not DB_CONFIG['password']:
        print("\n⚠️  警告: 数据库密码为空，请确认这是正确的配置")
    
    # 确认继续
    confirm = input("\n是否继续初始化数据库? (y/N): ").lower().strip()
    if confirm not in ['y', 'yes']:
        print("❌ 初始化已取消")
        sys.exit(0)
    
    # 创建数据库和表
    if create_database_and_tables():
        # 生成示例激活码
        generate_sample_codes()
        print("\n🎉 初始化完成！现在可以启动管理后台和API服务了。")
    else:
        print("\n❌ 初始化失败，请检查数据库配置和权限。")
        sys.exit(1)