#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3

def check_database():
    try:
        conn = sqlite3.connect('mozibang_activation.db')
        cursor = conn.cursor()
        
        # 检查所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("数据库中的表:", [t[0] for t in tables])
        
        # 检查activation_codes表结构
        if ('activation_codes',) in tables:
            cursor.execute("PRAGMA table_info(activation_codes)")
            columns = cursor.fetchall()
            print("activation_codes表结构:")
            for col in columns:
                print(f"  {col[1]} {col[2]}")
        
        # 检查pro_users表是否存在
        if ('pro_users',) in tables:
            cursor.execute("SELECT COUNT(*) FROM pro_users")
            count = cursor.fetchone()[0]
            print(f"pro_users表记录数: {count}")
            
            # 查看表结构
            cursor.execute("PRAGMA table_info(pro_users)")
            columns = cursor.fetchall()
            print("pro_users表结构:")
            for col in columns:
                print(f"  {col[1]} {col[2]}")
        else:
            print("pro_users表不存在!")
            
        conn.close()
        
    except Exception as e:
        print(f"检查数据库时出错: {e}")

if __name__ == "__main__":
    check_database()