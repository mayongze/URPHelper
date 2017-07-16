#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-07-05 16:53:19
# @Author  : mayongze (1014057907@qq.com)
# @Link    : https://github.com/mayongze
# @Version : 1.1.1.20170705

import sqlite3


class Sqlite3Helper(object):
    """docstring for DBHelper"""

    # conn = None
    # sqlite3 游标
    cursor = None
    file_name = None
    sql = None

    def __init__(self, dbFileName):
        self.file_name = dbFileName

    def open(self,check_same_thread = True):
        """
        打开数据库并设置游标
        """
        self.conn = sqlite3.connect(self.file_name,check_same_thread=check_same_thread)
        self.cursor = self.conn.cursor()
        return self

    def close(self):
        """
        关闭连接
        """
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def __del__(self):
        """
        析构
        """
        self.close()

    def commit(self):
        """
            提交事务
            SELECT语句不需要此操作，默认的execute方法的
            commit_at_once设为True会隐式调用此方法，
            否则就需要显示调用本方法。
        """
        self.conn.commit()

    def execute(self, sql=None, commit_at_once=True):
        """
            执行SQL语句
            参数:
                sql  要执行的SQL语句，若为None，则调用构造器生成的SQL语句。
                commit_at_once 是否立即提交事务，如果不立即提交，
                对于非查询操作，则需要调用commit显式提交。
        """
        if not sql:
            sql = self.sql

        self.cursor.execute(sql)
        if commit_at_once:
            self.commit()

    def fetchone(self, sql=None):
        """
            取一条记录
        """
        if not sql:
            sql = self.sql
        self.execute(sql, False)
        return self.cursor.fetchone()

    def fetchall(self, sql=None):
        """
            取所有记录
        """
        self.execute(sql, False)
        return self.cursor.fetchall()


def main():
    """
        主函数
    """
    pass

if __name__ == '__main__':
    main()
