-- 激活码系统数据库表结构设计

-- 1. 激活码表
CREATE TABLE activation_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(32) NOT NULL UNIQUE COMMENT '激活码',
    code_type ENUM('pro_lifetime', 'pro_1year', 'pro_6month') DEFAULT 'pro_lifetime' COMMENT '激活码类型',
    status ENUM('unused', 'used', 'expired', 'disabled') DEFAULT 'unused' COMMENT '状态',
    batch_id VARCHAR(50) NULL COMMENT '批次ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    expires_at DATETIME NULL COMMENT '过期时间（NULL表示永不过期）',
    used_at DATETIME NULL COMMENT '使用时间',
    used_by_user VARCHAR(255) NULL COMMENT '使用用户（Google邮箱）',
    notes TEXT NULL COMMENT '备注信息',
    INDEX idx_code (code),
    INDEX idx_status (status),
    INDEX idx_batch_id (batch_id),
    INDEX idx_used_by_user (used_by_user)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='激活码表';

-- 2. 用户Pro状态表
CREATE TABLE user_pro_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL UNIQUE COMMENT '用户邮箱',
    user_name VARCHAR(255) NULL COMMENT '用户姓名',
    is_pro BOOLEAN DEFAULT FALSE COMMENT '是否Pro用户',
    pro_type ENUM('lifetime', '1year', '6month') NULL COMMENT 'Pro类型',
    activated_at DATETIME NULL COMMENT '激活时间',
    expires_at DATETIME NULL COMMENT '到期时间（NULL表示永久）',
    activation_code VARCHAR(32) NULL COMMENT '使用的激活码',
    last_login DATETIME NULL COMMENT '最后登录时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_email (user_email),
    INDEX idx_is_pro (is_pro),
    INDEX idx_activation_code (activation_code),
    FOREIGN KEY (activation_code) REFERENCES activation_codes(code) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户Pro状态表';

-- 3. 激活码批次表
CREATE TABLE activation_batches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id VARCHAR(50) NOT NULL UNIQUE COMMENT '批次ID',
    batch_name VARCHAR(100) NOT NULL COMMENT '批次名称',
    code_type ENUM('pro_lifetime', 'pro_1year', 'pro_6month') DEFAULT 'pro_lifetime' COMMENT '激活码类型',
    total_count INT NOT NULL DEFAULT 0 COMMENT '总数量',
    used_count INT NOT NULL DEFAULT 0 COMMENT '已使用数量',
    created_by VARCHAR(100) NULL COMMENT '创建人',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    notes TEXT NULL COMMENT '批次备注',
    INDEX idx_batch_id (batch_id),
    INDEX idx_code_type (code_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='激活码批次表';

-- 4. 激活日志表
CREATE TABLE activation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    activation_code VARCHAR(32) NOT NULL COMMENT '激活码',
    user_email VARCHAR(255) NOT NULL COMMENT '用户邮箱',
    action ENUM('activate', 'verify', 'deactivate') NOT NULL COMMENT '操作类型',
    result ENUM('success', 'failed') NOT NULL COMMENT '操作结果',
    error_message TEXT NULL COMMENT '错误信息',
    ip_address VARCHAR(45) NULL COMMENT 'IP地址',
    user_agent TEXT NULL COMMENT '用户代理',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    INDEX idx_activation_code (activation_code),
    INDEX idx_user_email (user_email),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='激活日志表';

-- 插入一些示例数据
INSERT INTO activation_batches (batch_id, batch_name, code_type, total_count, created_by, notes) 
VALUES ('BATCH_001', '首批Pro永久激活码', 'pro_lifetime', 100, 'admin', '首次发布的永久Pro激活码');

-- 示例激活码（实际使用时应该用随机生成）
INSERT INTO activation_codes (code, code_type, batch_id, notes) VALUES 
('MOZIBANG-PRO-DEMO-001', 'pro_lifetime', 'BATCH_001', '演示用激活码1'),
('MOZIBANG-PRO-DEMO-002', 'pro_lifetime', 'BATCH_001', '演示用激活码2'),
('MOZIBANG-PRO-DEMO-003', 'pro_lifetime', 'BATCH_001', '演示用激活码3');