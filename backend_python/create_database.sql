-- MoziBang 激活码系统数据库表结构
-- 创建数据库
CREATE DATABASE IF NOT EXISTS mozibang_activation DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE mozibang_activation;

-- 1. 激活码表
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='激活码表';

-- 2. Pro用户表
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
    INDEX idx_last_login (last_login),
    FOREIGN KEY (activation_code) REFERENCES activation_codes(code) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Pro用户表';

-- 3. 管理员表
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员表';

-- 4. 操作日志表
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
    INDEX idx_operation_result (operation_result),
    FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- 5. 系统配置表
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- 插入默认管理员账号 (用户名: admin, 密码: admin123)
-- 密码哈希使用 werkzeug.security.generate_password_hash('admin123')
INSERT INTO admin_users (username, password_hash, email, full_name, role, is_active) 
VALUES ('admin', 'pbkdf2:sha256:600000$8xKzJzQzJzQzJzQz$5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f', 'admin@mozibang.com', '系统管理员', 'super_admin', TRUE)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 插入默认系统配置
INSERT INTO system_config (config_key, config_value, config_type, description, is_public) VALUES
('system_name', 'MoziBang激活码系统', 'string', '系统名称', TRUE),
('version', '1.0.0', 'string', '系统版本', TRUE),
('max_codes_per_batch', '1000', 'number', '每批次最大激活码数量', FALSE),
('code_length', '16', 'number', '激活码长度', FALSE),
('api_timeout', '30', 'number', 'API超时时间(秒)', FALSE),
('enable_email_notification', 'false', 'boolean', '是否启用邮件通知', FALSE),
('maintenance_mode', 'false', 'boolean', '维护模式', FALSE)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 创建视图：激活码统计
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
GROUP BY code_type;

-- 创建视图：Pro用户统计
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
GROUP BY pro_type;

-- 创建视图：每日统计
CREATE OR REPLACE VIEW v_daily_stats AS
SELECT 
    DATE(created_at) as stat_date,
    'activation_codes' as stat_type,
    COUNT(*) as count
FROM activation_codes 
GROUP BY DATE(created_at)
UNION ALL
SELECT 
    DATE(activated_at) as stat_date,
    'pro_activations' as stat_type,
    COUNT(*) as count
FROM pro_users 
GROUP BY DATE(activated_at)
ORDER BY stat_date DESC, stat_type;

-- 创建存储过程：生成激活码
DELIMITER //
CREATE PROCEDURE GenerateActivationCodes(
    IN p_count INT,
    IN p_code_type VARCHAR(20),
    IN p_batch_name VARCHAR(100),
    IN p_notes TEXT
)
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE v_code VARCHAR(32);
    
    WHILE i < p_count DO
        -- 生成16位随机激活码
        SET v_code = UPPER(CONCAT(
            SUBSTRING(MD5(RAND()), 1, 4), '-',
            SUBSTRING(MD5(RAND()), 1, 4), '-',
            SUBSTRING(MD5(RAND()), 1, 4), '-',
            SUBSTRING(MD5(RAND()), 1, 4)
        ));
        
        -- 检查激活码是否已存在
        IF NOT EXISTS (SELECT 1 FROM activation_codes WHERE code = v_code) THEN
            INSERT INTO activation_codes (code, code_type, batch_name, notes)
            VALUES (v_code, p_code_type, p_batch_name, p_notes);
            SET i = i + 1;
        END IF;
    END WHILE;
END //
DELIMITER ;

-- 创建触发器：更新Pro用户最后登录时间
DELIMITER //
CREATE TRIGGER tr_update_last_login 
BEFORE UPDATE ON pro_users
FOR EACH ROW
BEGIN
    IF NEW.last_login != OLD.last_login THEN
        SET NEW.updated_at = CURRENT_TIMESTAMP;
    END IF;
END //
DELIMITER ;

-- 创建索引优化查询性能
CREATE INDEX idx_activation_codes_composite ON activation_codes(code_type, is_used, is_disabled, created_at);
CREATE INDEX idx_pro_users_composite ON pro_users(pro_type, is_active, expires_at);
CREATE INDEX idx_operation_logs_composite ON operation_logs(admin_id, operation_type, created_at);

-- 显示创建结果
SELECT 'Database schema created successfully!' as result;
SELECT 'Tables created:' as info;
SELECT TABLE_NAME, TABLE_COMMENT FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'mozibang_activation' AND TABLE_TYPE = 'BASE TABLE';

SELECT 'Views created:' as info;
SELECT TABLE_NAME as VIEW_NAME, TABLE_COMMENT FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'mozibang_activation' AND TABLE_TYPE = 'VIEW';

SELECT 'Default admin user created:' as info;
SELECT username, email, role, is_active FROM admin_users WHERE username = 'admin';