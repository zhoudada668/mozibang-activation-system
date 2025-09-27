#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MoziBang 激活码系统统计报表模块
提供详细的激活码使用统计和报表功能
"""

import sqlite3
import pymysql
import json
import datetime
from collections import defaultdict
import os

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'mozibang_activation.db')

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class ActivationStatistics:
    """激活码统计类"""
    
    def __init__(self, db_connection=None):
        """初始化统计类，支持传入外部数据库连接"""
        if db_connection:
            self.conn = db_connection
            self.is_mysql = True
        else:
            self.conn = get_db_connection()
            self.is_mysql = False
    
    def __del__(self):
        # 如果是外部传入的连接，不要关闭它
        if hasattr(self, 'conn') and not self.is_mysql:
            self.conn.close()
    
    def get_activation_overview(self):
        """获取激活码总览统计"""
        cursor = self.conn.cursor()
        
        # 激活码总体统计
        cursor.execute("""
            SELECT 
                code_type,
                COUNT(*) as total_codes,
                SUM(CASE WHEN is_used = 1 THEN 1 ELSE 0 END) as used_codes,
                SUM(CASE WHEN is_used = 0 AND is_disabled = 0 THEN 1 ELSE 0 END) as available_codes,
                SUM(CASE WHEN is_disabled = 1 THEN 1 ELSE 0 END) as disabled_codes
            FROM activation_codes 
            GROUP BY code_type
            ORDER BY code_type
        """)
        
        code_stats = []
        for row in cursor.fetchall():
            code_stats.append({
                'code_type': row['code_type'],
                'total_codes': row['total_codes'],
                'used_codes': row['used_codes'],
                'available_codes': row['available_codes'],
                'disabled_codes': row['disabled_codes'],
                'usage_rate': round((row['used_codes'] / row['total_codes']) * 100, 2) if row['total_codes'] > 0 else 0
            })
        
        return code_stats
    
    def get_user_statistics(self):
        """获取用户统计"""
        cursor = self.conn.cursor()
        
        # Pro用户统计
        cursor.execute("""
            SELECT 
                pro_type,
                COUNT(*) as total_users,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_users,
                SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive_users,
                SUM(CASE WHEN expires_at IS NULL THEN 1 ELSE 0 END) as lifetime_users,
                SUM(CASE WHEN expires_at IS NOT NULL AND expires_at > datetime('now') THEN 1 ELSE 0 END) as valid_users,
                SUM(CASE WHEN expires_at IS NOT NULL AND expires_at <= datetime('now') THEN 1 ELSE 0 END) as expired_users
            FROM pro_users 
            GROUP BY pro_type
            ORDER BY pro_type
        """)
        
        user_stats = []
        for row in cursor.fetchall():
            user_stats.append({
                'pro_type': row['pro_type'],
                'total_users': row['total_users'],
                'active_users': row['active_users'],
                'inactive_users': row['inactive_users'],
                'lifetime_users': row['lifetime_users'],
                'valid_users': row['valid_users'],
                'expired_users': row['expired_users']
            })
        
        return user_stats
    
    def get_daily_activation_trend(self, days=30):
        """获取每日激活趋势（最近N天）"""
        cursor = self.conn.cursor()
        
        if self.is_mysql:
            # MySQL语法
            cursor.execute("""
                SELECT 
                    DATE(activated_at) as activation_date,
                    COUNT(*) as activation_count,
                    COUNT(DISTINCT user_email) as unique_users
                FROM pro_users 
                WHERE activated_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY DATE(activated_at)
                ORDER BY activation_date DESC
            """, (days,))
        else:
            # SQLite语法
            cursor.execute("""
                SELECT 
                    DATE(activated_at) as activation_date,
                    COUNT(*) as activation_count,
                    COUNT(DISTINCT user_email) as unique_users
                FROM pro_users 
                WHERE activated_at >= datetime('now', '-{} days')
                GROUP BY DATE(activated_at)
                ORDER BY activation_date DESC
            """.format(days))
        
        trend_data = []
        for row in cursor.fetchall():
            if self.is_mysql:
                trend_data.append({
                    'date': str(row['activation_date']),
                    'activations': row['activation_count'],
                    'unique_users': row['unique_users']
                })
            else:
                trend_data.append({
                    'date': row['activation_date'],
                    'activations': row['activation_count'],
                    'unique_users': row['unique_users']
                })
        
        return trend_data
    
    def get_code_type_distribution(self):
        """获取激活码类型分布"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                ac.code_type,
                COUNT(pu.id) as activated_count,
                AVG(CASE 
                    WHEN pu.expires_at IS NULL THEN NULL 
                    ELSE (julianday(pu.expires_at) - julianday(pu.activated_at))
                END) as avg_duration_days
            FROM activation_codes ac
            LEFT JOIN pro_users pu ON ac.code = pu.activation_code
            WHERE ac.is_used = 1
            GROUP BY ac.code_type
            ORDER BY activated_count DESC
        """)
        
        distribution = []
        for row in cursor.fetchall():
            distribution.append({
                'code_type': row['code_type'],
                'activated_count': row['activated_count'],
                'avg_duration_days': round(row['avg_duration_days'], 1) if row['avg_duration_days'] else None
            })
        
        return distribution
    
    def get_user_activity_report(self):
        """获取用户活动报告"""
        cursor = self.conn.cursor()
        
        # 最近激活的用户
        cursor.execute("""
            SELECT 
                user_email,
                user_name,
                pro_type,
                activation_code,
                activated_at,
                expires_at,
                is_active,
                last_login
            FROM pro_users 
            ORDER BY activated_at DESC 
            LIMIT 20
        """)
        
        recent_activations = []
        for row in cursor.fetchall():
            recent_activations.append({
                'user_email': row['user_email'],
                'user_name': row['user_name'],
                'pro_type': row['pro_type'],
                'activation_code': row['activation_code'],
                'activated_at': row['activated_at'],
                'expires_at': row['expires_at'],
                'is_active': bool(row['is_active']),
                'last_login': row['last_login']
            })
        
        # 即将过期的用户
        cursor.execute("""
            SELECT 
                user_email,
                user_name,
                pro_type,
                expires_at,
                (julianday(expires_at) - julianday('now')) as days_until_expiry
            FROM pro_users 
            WHERE expires_at IS NOT NULL 
            AND expires_at > datetime('now')
            AND expires_at <= datetime('now', '+30 days')
            ORDER BY expires_at ASC
        """)
        
        expiring_soon = []
        for row in cursor.fetchall():
            expiring_soon.append({
                'user_email': row['user_email'],
                'user_name': row['user_name'],
                'pro_type': row['pro_type'],
                'expires_at': row['expires_at'],
                'days_until_expiry': int(row['days_until_expiry'])
            })
        
        return {
            'recent_activations': recent_activations,
            'expiring_soon': expiring_soon
        }
    
    def get_revenue_estimation(self):
        """获取收入估算（基于激活码类型）"""
        # 假设的价格映射
        price_mapping = {
            'pro_lifetime': 299.0,
            'pro_1year': 99.0,
            'pro_6month': 59.0
        }
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                ac.code_type,
                COUNT(pu.id) as activated_count
            FROM activation_codes ac
            LEFT JOIN pro_users pu ON ac.code = pu.activation_code
            WHERE ac.is_used = 1
            GROUP BY ac.code_type
        """)
        
        revenue_data = []
        total_revenue = 0
        
        for row in cursor.fetchall():
            code_type = row['code_type']
            count = row['activated_count']
            price = price_mapping.get(code_type, 0)
            revenue = count * price
            total_revenue += revenue
            
            revenue_data.append({
                'code_type': code_type,
                'activated_count': count,
                'unit_price': price,
                'total_revenue': revenue
            })
        
        return {
            'revenue_by_type': revenue_data,
            'total_estimated_revenue': total_revenue
        }
    
    def generate_comprehensive_report(self):
        """生成综合报告"""
        report = {
            'generated_at': datetime.datetime.now().isoformat(),
            'activation_overview': self.get_activation_overview(),
            'user_statistics': self.get_user_statistics(),
            'daily_trend': self.get_daily_activation_trend(30),
            'code_distribution': self.get_code_type_distribution(),
            'user_activity': self.get_user_activity_report(),
            'revenue_estimation': self.get_revenue_estimation()
        }
        
        return report
    
    def export_report_to_json(self, filename=None):
        """导出报告为JSON文件"""
        if filename is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'activation_report_{timestamp}.json'
        
        report = self.generate_comprehensive_report()
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return filepath

def main():
    """主函数 - 生成示例报告"""
    print("📊 MoziBang 激活码系统统计报告")
    print("=" * 50)
    
    stats = ActivationStatistics()
    
    # 激活码总览
    print("\n🎫 激活码总览:")
    overview = stats.get_activation_overview()
    for item in overview:
        print(f"  {item['code_type']}: 总计{item['total_codes']}, 已用{item['used_codes']}, 可用{item['available_codes']}, 使用率{item['usage_rate']}%")
    
    # 用户统计
    print("\n👥 用户统计:")
    user_stats = stats.get_user_statistics()
    for item in user_stats:
        print(f"  {item['pro_type']}: 总计{item['total_users']}, 活跃{item['active_users']}, 永久{item['lifetime_users']}")
    
    # 每日趋势
    print("\n📈 最近7天激活趋势:")
    trend = stats.get_daily_activation_trend(7)
    for item in trend[:7]:
        print(f"  {item['date']}: {item['activations']}次激活, {item['unique_users']}个用户")
    
    # 收入估算
    print("\n💰 收入估算:")
    revenue = stats.get_revenue_estimation()
    for item in revenue['revenue_by_type']:
        print(f"  {item['code_type']}: {item['activated_count']}个 × ¥{item['unit_price']} = ¥{item['total_revenue']}")
    print(f"  总计估算收入: ¥{revenue['total_estimated_revenue']}")
    
    # 导出完整报告
    print("\n📄 导出完整报告...")
    filepath = stats.export_report_to_json()
    print(f"✅ 报告已导出到: {filepath}")

if __name__ == '__main__':
    main()