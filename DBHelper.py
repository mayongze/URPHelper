#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-07-05 16:53:19
# @Author  : mayongze (1014057907@qq.com)
# @Link    : https://github.com/mayongze
# @Version : 1.1.1.20170705

import sqlite3
import os

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
        dir = os.path.dirname(self.file_name)
        if not os.path.isdir(dir):
            os.mkdir(dir)
        self.conn = sqlite3.connect(self.file_name,check_same_thread=check_same_thread)
        self.cursor = self.conn.cursor()
        self.creatTable()
        # 关闭写同步
        # self.execute("PRAGMA synchronous = OFF;")
        return self

    def creatTable(self):
        """
        创建数据库表
        """
        course = '''
                    CREATE TABLE "course" (
                    "c_no"  TEXT NOT NULL,
                    "c_name"  TEXT,
                    "c_credit"  TEXT,
                    "c_property"  TEXT,
                    "c_highest_score"  TEXT,
                    "c_lowest_score"  TEXT,
                    "c_average_score"  TEXT,
                    PRIMARY KEY ("c_no")
                    );
                '''
        course_time = '''
                    CREATE TABLE "course_time" (
                    "id"  INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL DEFAULT 1,
                    "weekfrom"  INTEGER,
                    "weekto"  INTEGER,
                    "stopfrom"  INTEGER,
                    "stopto"  INTEGER,
                    "weektype"  INTEGER,
                    "day"  INTEGER,
                    "lesson"  INTEGER,
                    "courseid"  TEXT,
                    "num"  TEXT,
                    "teacher"  TEXT,
                    "campus"  TEXT,
                    "bld"  TEXT,
                    "place"  TEXT
                    );
                '''
        elective = '''
                    CREATE TABLE "elective" (
                    "id"  INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL DEFAULT 0,
                    "semester"  TEXT,
                    "s_no"  INTEGER,
                    "elective_course_time_id"  INTEGER
                    );
                '''
        grade = '''
                    CREATE TABLE "grade" (
                    "sno"  INTEGER NOT NULL,
                    "cno"  TEXT NOT NULL,
                    "cnum"  TEXT,
                    "grade"  TEXT NOT NULL,
                    "rank"  TEXT,
                    "semester"  TEXT,
                    "flunkcount"  INTEGER DEFAULT 0,
                    PRIMARY KEY ("sno" ASC, "cno" ASC)
                    );
                '''
        students = '''
                    CREATE TABLE "students" (
                    "sno"  INTEGER,
                    "s_passwd"  TEXT,
                    "s_name"  TEXT,
                    "s_sex"  TEXT,
                    "s_sfz"  TEXT,
                    "s_birth"  TEXT,
                    "s_highschool"  TEXT,
                    "s_addr"  TEXT,
                    "s_major"  TEXT,
                    "s_depatment"  TEXT,
                    "s_class"  TEXT,
                    "s_nemtgrade"  TEXT,
                    "s_nemtid"  TEXT,
                    "s_ethnicity"  TEXT,
                    "s_recorddate"  TEXT,
                    "s_politicalstatus"  TEXT,
                    "s_admissiondate"  INTEGER,
                    "s_education"  TEXT,
                    "s_status"  TEXT,
                    PRIMARY KEY ("sno" ASC)
                    );
                 '''
        syllabus = '''
                    CREATE TABLE "syllabus" (
                    "id"  INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL DEFAULT 0,
                    "s_class"  TEXT,
                    "course_time_id"  INTEGER,
                    "semester"  TEXT
                    );
                '''
        syllabusUnique = '''
                    CREATE UNIQUE INDEX "main"."idx_s_class_course_time_id"
                    ON "syllabus" ("s_class" ASC, "course_time_id" ASC);
                    '''
        tableList = [course,course_time,elective,grade,students,syllabus,syllabusUnique]

        for item in tableList:
            try:
                self.execute(item)
            except Exception as e:
                pass
                # print('Table create error!')
        self.commit()  

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
    dbHepler = Sqlite3Helper('database\demodatabase.db')
    dbHepler.open(check_same_thread=False)
    pass

if __name__ == '__main__':
    main()
