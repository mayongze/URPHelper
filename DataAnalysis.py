#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-07-05 16:53:19
# @Author  : mayongze (1014057907@qq.com)
# @Link    : https://github.com/mayongze
# @Version : 1.1.1.20170705

import os
import URPCrawlerDAO
import URPMain
import DBHelper 
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math
from pylab import *  
# 不设置字体plt 标签不能显示中文
mpl.rcParams['font.sans-serif'] = ['SimHei']  


def flunk_pie(cname,sex = None): 
    strSql = "SELECT s.s_sex,sum(CASE WHEN g.grade >= 60 THEN 1 ELSE 0 END) AS 及格人数,sum( CASE WHEN g.grade < 60 THEN 1 ELSE 0 END ) AS 不及格人数,sum( CASE WHEN 1=1 THEN 1 ELSE 0 END ) AS 没有成绩人数 FROM grade as g ,students as s,course WHERE g.semester = '2016-2017-2' AND s.sno = g.sno AND course.c_name = '{0}'  AND g.semester = '2016-2017-2' AND course.c_no = g.cno GROUP BY s_sex".format(cname)
    if sex:
        title = "2016-2017 春季学期 %s(%s) 成绩统计" %(cname,sex)
    else:
        sex = 0
        title = "2016-2017 春季学期 %s 成绩统计" %cname

    dic = {}
    resultList = dbHepler.fetchall(strSql)
    for item in resultList:
        dic[item[0]] = item[1:]
    print(dic)
    if '男' not in dic:
        dic['男']=[0,0,0]
    if '女' not in dic:
        dic['女']=[0,0,0]

    X = [dic['男'][0],dic['女'][0],dic['男'][1],dic['女'][1]]  
    labels=['(男)及格-%s人'%X[0],'(女)及格-%s人'%X[1],'(男)不及格-%s人'%X[2],'(女)不及格-%s人'%X[3]] 
    expl = [0,0,0.01,0.01]   #第二块即China离开圆心0.1
    colors  = ["blue","red","coral","green"]  #设置颜色（循环显示）  
    #fig = plt.figure() 
    plt.figure(1, figsize=(7,6)) # 正方形图
    plt.title(title) 
    plt.pie(X,labels=labels,explode=expl, colors=colors,autopct='%1.2f%%',pctdistance=0.8, shadow=True) #画饼图（数据，数据对应的标签，百分数保留两位小数点）
    plt.show() 
    
def flunkCourseRank_barh():
    strSql = "SELECT course.c_name,count(g.grade) FROM grade AS g,course WHERE g.semester = '2016-2017-2' AND g.flunkcount > 0 AND g.cno = course.c_no GROUP BY course.c_name ORDER BY count(g.cno) DESC"
    tmp = dbHepler.fetchall(strSql)
    courseList,grade = [],[]
    for item in tmp:
        #if int(item[1]) > 5:
        courseList.append(item[0])
        grade.append(item[1])

    label = courseList
    x = grade
 
    idx = np.arange(len(x))
    color = cm.jet(np.array(x)/max(x))
    plt.barh(idx, x, color=color)
    #plt.yticks(idx+1,label)

    plt.yticks(idx,label,fontsize=5)
    plt.grid(axis='x')
 
    plt.xlabel('不及格人数')
    plt.ylabel('科目')
    plt.title('2016-2017 春季学期 不及格科目')
 
    plt.show()

def flunkMajorStatistics(majorKey):

    majorKey = 'C14'
    strSql = "SELECT s.s_major,sum(CASE WHEN g.isFlunk = 1 THEN 1 ELSE 0 END)  as 挂科人数,sum(CASE WHEN g.isFlunk = 0 THEN 1 ELSE 0 END)  as 没挂过科人数,sum(CASE WHEN 1 = 1 THEN 1 ELSE 0 END)  as 总人数 FROM (SELECT g.sno,( CASE WHEN sum(CASE WHEN g.grade < 60 and g.grade !='' THEN 1 ELSE 0 END ) > 0 THEN 1 ELSE 0 END ) AS isFlunk FROM grade AS g WHERE g.semester = '2016-2017-2' GROUP BY g.sno ORDER BY g.sno ASC ) AS g, students AS s WHERE s.sno = g.sno AND s.s_class LIKE '%{0}%' GROUP BY s_major".format(majorKey)
    tmp = dbHepler.fetchall(strSql)

    C14major={}
    for item in tmp:
       C14major[item[0].rstrip("（城市学院）")] =  int(item[1]) / (int(item[2]) + int(item[1]))

    majorKey = 'C15'
    strSql = "SELECT s.s_major,sum(CASE WHEN g.isFlunk = 1 THEN 1 ELSE 0 END)  as 挂科人数,sum(CASE WHEN g.isFlunk = 0 THEN 1 ELSE 0 END)  as 没挂过科人数,sum(CASE WHEN 1 = 1 THEN 1 ELSE 0 END)  as 总人数 FROM (SELECT g.sno,( CASE WHEN sum(CASE WHEN g.grade < 60 and g.grade !='' THEN 1 ELSE 0 END ) > 0 THEN 1 ELSE 0 END ) AS isFlunk FROM grade AS g WHERE g.semester = '2016-2017-2' GROUP BY g.sno ORDER BY g.sno ASC ) AS g, students AS s WHERE s.sno = g.sno AND s.s_class LIKE '%{0}%' GROUP BY s_major".format(majorKey)
    tmp = dbHepler.fetchall(strSql)

    C15major={}
    for item in tmp:
       C15major[item[0].rstrip("（城市学院）")] =  int(item[1]) / (int(item[2]) + int(item[1]))

    majorKey = 'C16'
    strSql = "SELECT s.s_major,sum(CASE WHEN g.isFlunk = 1 THEN 1 ELSE 0 END)  as 挂科人数,sum(CASE WHEN g.isFlunk = 0 THEN 1 ELSE 0 END)  as 没挂过科人数,sum(CASE WHEN 1 = 1 THEN 1 ELSE 0 END)  as 总人数 FROM (SELECT g.sno,( CASE WHEN sum(CASE WHEN g.grade < 60 and g.grade !='' THEN 1 ELSE 0 END ) > 0 THEN 1 ELSE 0 END ) AS isFlunk FROM grade AS g WHERE g.semester = '2016-2017-2' GROUP BY g.sno ORDER BY g.sno ASC ) AS g, students AS s WHERE s.sno = g.sno AND s.s_class LIKE '%{0}%' GROUP BY s_major".format(majorKey)
    tmp = dbHepler.fetchall(strSql)

    C16major={}
    for item in tmp:
       C16major[item[0].rstrip("（城市学院）")] =  int(item[1]) / (int(item[2]) + int(item[1]))


    s14 = pd.Series(C14major)
    s15 = pd.Series(C15major)
    s16 = pd.Series(C16major)
    df = pd.DataFrame([s14,s15,s16])
    df = df.fillna(0)
    idx = np.arange(len(df.columns))
    idx1 = [i+0.3 for i in idx]
    idx2 = [i+0.3 for i in idx1]
    plt.figure(figsize=(10, 6))
    plt.bar(idx,df.values[0],color='g',width = .3,alpha=0.7,label='C14级')
    plt.bar(idx1,df.values[1],color='r',width = .3,alpha=0.7,label='C15级')
    plt.bar(idx2,df.values[2],color='b',width = .3,alpha=0.7,label='C16级')
    #idx = np.arange(len(x))
    #idx = np.arange(0,1)
    #color = cm.jet(np.array(x)/max(x))
    #plt.bar(idx, x, color=color)
    plt.ylim(0,1)
    # axis=y 在y轴显示网格线
    plt.grid(color='#000000',linestyle='-.',axis='y',linewidth=0.8,alpha=0.4)

    # plt.xlabel('专业')
    plt.ylabel('百分比')
    plt.title('(2016-2017)春季学期专业挂科率统计')
    plt.legend(loc='upper right')

    plt.xticks(range(len(df.columns)),list(df.columns),fontsize=7)
    plt.show()

if __name__ == '__main__':

    dbHepler = DBHelper.Sqlite3Helper('demodatabase.db')
    dbHepler.open(check_same_thread=False)
    flunk_pie('高等数学(一)B',None)
    flunkCourseRank_barh()
    #flunkMajorStatistics("")
    
    role = None
    gradeList = URPCrawlerDAO.StudentsGradeDao(role, dbHepler).getNowSemesterGrade('高等数学(一)B','2016-2017-2')
    gradeList = [int(float(i[0])) for i in gradeList]     #成绩数据
    mu = np.mean(gradeList)      #平均值
    sigma = np.std(gradeList)    #标准差
    data = np.random.normal(mu,sigma,100)  #生成正态分布随机数据
    x = np.linspace(0,100,100)
    y = (1. / math.sqrt(2 * np.pi) / sigma)*np.exp( -((x-mu)**2/(2*sigma**2)) )
    plt.hist(data,bins=100,facecolor='g',alpha=0.44)
    plt.hist(gradeList,bins=70,facecolor='r',histtype='stepfilled')
    plt.plot(x,y,color='b')   #正态分布曲线
    plt.xlabel('成绩')
    plt.ylabel('人数')
    plt.title('2016-2017春季学期 高等数学(一)B')
    plt.show()
    
    '''
    label = ["大学英语（四级）", "Java程序设计", "计算机组成","操作系统"] 
    tmp = URPCrawlerDAO.StudentsGradeDao(None, dbHepler).getNowSemesterGrade('大学英语（四级）','2016-2017-2')
    snoList,gradeList = [],[]
    for sno,grade in tmp:
        snoList.append(int(sno))
        gradeList.append(float(grade))
    plt.plot(snoList,gradeList,linewidth=1.2)
    tmp = URPCrawlerDAO.StudentsGradeDao(None, dbHepler).getNowSemesterGrade('Java程序设计','2016-2017-2')
    snoList,gradeList = [],[]
    for sno,grade in tmp:
        snoList.append(int(sno))
        gradeList.append(float(grade))
    plt.plot(snoList,gradeList,linewidth=1.2)
    tmp = URPCrawlerDAO.StudentsGradeDao(None, dbHepler).getNowSemesterGrade('计算机组成','2016-2017-2')
    snoList,gradeList = [],[]
    for sno,grade in tmp:
        snoList.append(int(sno))
        gradeList.append(float(grade))
    plt.plot(snoList,gradeList,linewidth=1.2)
    tmp = URPCrawlerDAO.StudentsGradeDao(None, dbHepler).getNowSemesterGrade('操作系统','2016-2017-2')
    snoList,gradeList = [],[]
    for sno,grade in tmp:
        snoList.append(int(sno))
        gradeList.append(float(grade))
    plt.plot(snoList,gradeList,linewidth=1.2)
    #plt.legend(loc = 'lower right')
    #添加图表网格线，设置网格线颜色，线形，宽度和透明度
    plt.grid( True,color='#000000',linestyle='--', linewidth=0.8,axis='both',alpha=0.4)
    plt.legend(label, loc = 0, ncol = 2) 
    ax = plt.gca()
    plt.xlabel('学号')
    plt.ylabel('成绩')
    ax.set_facecolor('#e5e5e5')
    plt.title('2016-2017春季学期 计科软件专业C15级期末成绩折线图')
    # ax.set_facecolor((1, 0, 0))
    plt.show() 
    '''