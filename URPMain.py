#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-07-05 16:53:19
# @Author  : mayongze (1014057907@qq.com)
# @Link    : https://github.com/mayongze
# @Version : 1.1.1.20170705

import os
import DBHelper
import URPCrawlerDAO
import random
import requests
import pytesseract
import re
import time
import urllib.request
from PIL import Image, ImageEnhance
import matplotlib.pyplot as plt
from io import BytesIO
import sqlite3
import copy
import NETinterface as NET
import queue
import threading
import traceback

# 异常错误类
class MyURPHtmlErr(Exception):
    html = None

    def __init__(self, html):
        Exception.__init__(self)
        self.html = html
        self.message = self.htmlErrMeg()

    def htmlErrMeg(self):
        m = re.search(
            r'<td class="errorTop">.*?<font color="#990000">(.*?)</font>', self.html, re.S)
        return m.group(1)


class Role(object):
    """
    角色操作类
    """
    # 教务URL
    eduUrl = None
    # requests 的Session对象
    ression = None
    # 学号
    userId = None
    # 密码
    passWd = None
    # 当前学年度
    semester = None
    # 班级
    dClass = None
    # 课程表信息
    _CourseList = None
    # 学生全部成绩信息
    _AllGrade = None
    # 本学期成绩信息
    _NowSemesterGrade = None
    # 本学期不及格成绩信息
    _NowSemesterFlunkGrade = None
    # 学籍信息
    _XJInfo = None
    # 错误信息列表
    _ERRORList = None
    # 不及格信息
    _CurrentFlunkGrade = None
    # 现在不及格数
    _CurrentFlunkCount = None
    # 曾经不及格数
    _OnceFlunkCount = None

    def __init__(self, userId, passWd):
        self.ression = requests.Session()
        self.userId = userId
        self.passWd = passWd

    # 获取图像
    def getImage(self, imgUrl):
        r = self.ression.get(imgUrl, stream=True)
        image = Image.open(BytesIO(r.content))
        return image

        '''
        extension = os.path.splitext(imgUrl)[1]  # 获取扩展名
        imgName = ''.join(["./image", extension])
        with open(imgName, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()
            f.close()

        return imgName
        '''

    # 下载验证码
    def downLoadAutoCode(self):
        img = self.getImage(
            "%s/validateCodeAction.do?random=%f" % (Role.eduUrl,random.random()))
        #img = Image.open('11.tiff')
        img = img.convert('L')  # 将彩色图像转化为灰度图

        threshold = 140
        table = []
        for i in range(256):
            if i < threshold:
                table.append(0)
            else:
                table.append(1)

        img = img
        #img.save('%s.tiff' % name,'TIFF')
        '''
        img = ImageEnhance.Color(img)
        img = img.enhance(0.5)
        '''

        img = ImageEnhance.Brightness(img)
        img = img.enhance(1.8)
        img = ImageEnhance.Contrast(img)
        img = img.enhance(8)
        img = ImageEnhance.Sharpness(img)
        img = img.enhance(0.05)

        img = img

        # img = img.point(table, '1') #降噪，图片二值化
        pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract'
        code = pytesseract.image_to_string(img, lang='eng', config="-psm 7")
        # 去掉非法字符，只保留字母数字

        code = re.sub("\W", "", code)
        print(code)
        img.save('%s.tiff' % code, 'TIFF')

        # plt.figure("img")
        # plt.imshow(img)
        # plt.show()

    # 下载角色照片
    def downLoadPhoto(self):
        r = self.ression.get("%s/xjInfoAction.do?oper=img" % Role.eduUrl)

        imgName = os.path.join('Photo', "%s.jpg" % self.userId)
        if not os.path.isdir('Photo'):
            os.mkdir('Photo')

        with open(imgName, 'wb') as f:
            f.write(r.content)
            f.flush()
            f.close()

    # 获取验证码
    def getAuthCode(self):
        img = self.getImage(
            "%s/validateCodeAction.do?random=%f" % (Role.eduUrl,random.random()))

        # img = img.save("Wq7T.png","PNG")
        # img = Image.open("bnZr.png")
        img = img.convert('L')  # 将彩色图像转化为灰度图
        # img = img.point(initTable(), '1') #降噪，图片二值化

        # img = ImageEnhance.Color(img)
        # img = img.enhance(0.5)

        img = ImageEnhance.Brightness(img)
        img = img.enhance(1.8)
        img = ImageEnhance.Contrast(img)
        img = img.enhance(8)
        img = ImageEnhance.Sharpness(img)
        img = img.enhance(0.05)

        # img.save("123.png","PNG")
        pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract'
        code = pytesseract.image_to_string(img, lang='eng', config="-psm 7")
        # 去掉非法字符，只保留字母数字
        code = re.sub("\W", "", code)

        # plt.figure("img")
        # plt.imshow(img)
        # plt.show()
        # print(code)
        return code

    # 获取课程表
    def getCourse(self):
        r = self.ression.get("%s/xkAction.do?actionType=6" % Role.eduUrl)
        html = r.text
        pattern = re.compile(r'<tr class=.*?</tr>', re.S)

        # 这里用数组不用迭代器了
        result = re.findall(pattern, r.text)

        courseList = []
        trIndex = 0
        while trIndex < len(result):
            text = result[trIndex]
            # 先判断有列数
            rowspan = None

            if rowspan == None:
                m = re.search(r'<td rowspan="(\d)"', text)
                if m == None:
                    rowspan = 0
                else:
                    rowspan = int(m.group(1))

            idx = 0
            tempList = ['培养方案', '课程号', '课程名', '课序号', '学分', '课程属性',
                        '考试类型', '教师', '修读方式', '选课状态', '周次', '星期', '节次', '节数', '校区', '教学楼', '教室']
            temp = dict.fromkeys(tempList)
            # 此处应该为19但是 大纲日历 列 跳过所以为18
            for j in range(0, 17):
                idx = text.find(r'&nbsp;', idx)  # 从begin位置开始搜索
                end = text.find(r'</td>', idx)
                temp[tempList[j]] = text[idx + 6:end].strip()
                idx = end
            courseList.append(temp)
            for i in range(1, rowspan):
                idx = 0
                # 新行还是上门课的信息 一行课程可能有多行上课时间
                trIndex = trIndex + 1
                text = result[trIndex]
                temp = copy.deepcopy(temp)
                for j in range(10, 17):
                    idx = text.find(r'&nbsp;', idx)
                    end = text.find(r'</td>', idx)
                    temp[tempList[j]] = text[idx + 6:end].strip()
                    idx = end
                courseList.append(temp)

            trIndex = trIndex + 1

        # self.courseList = courseList
        return courseList

    # 模拟登陆
    def login(self):

        code = self.getAuthCode()
        # 表单
        payload = {'zjh1': '',
                   'tips': '',
                   'lx': '',
                   'evalue': '',
                   'eflag': '',
                   'fs': '',
                   'dzslh': '',
                   'zjh': self.userId,
                   'mm': self.passWd,
                   'v_yzm': code}

        r = self.ression.post(
            "%s/loginAction.do" % Role.eduUrl, data=payload)

        autoCode = 0

        while r.text.find('你输入的验证码错误，请您重新输入！') != -1:
            autoCode = autoCode + 1
            payload['v_yzm'] = self.getAuthCode()
            r = self.ression.post(
                "%s/loginAction.do" % Role.eduUrl, data=payload)

        # print('AutoCode Err Count:%d' % autoCode)

        if (r.text.find('学分制综合教务') == -1):
            raise MyURPHtmlErr(r.text)

    # 获取学籍信息
    def getXJInfo(self):
        r = self.ression.get(
            '%s/xjInfoAction.do?oper=xjxx' % Role.eduUrl)
        pattern = re.compile(
            r'<td class="fieldName" width="180">(.*?):&nbsp.*?">(.*?)</td>', re.S)
        result = re.finditer(pattern, r.text)
        xjinfo = {}
        for i in result:
            key = i.group(1).strip()
            value = i.group(2).strip()
            xjinfo[key] = value
        self.dClass = xjinfo['班级']
        return xjinfo

    # 获取全部成绩
    def getAllGrade(self):
        r = self.ression.get(
            '%s/gradeLnAllAction.do?type=ln&oper=sxinfo&lnsxdm=001' % Role.eduUrl)

        pattern = re.compile(r'<tr class="[a-zA-Z]+.*?(<td.*?)</tr>', re.S)
        result = re.finditer(pattern, r.text)
        allGrade = []
        for i in result:
            text = i.group(1)
            idx = 0
            tempList = ['课程号', '课序号', '课程名', '英文课程名', '学分', '课程属性', '成绩','考试时间']
            temp = dict.fromkeys(tempList)

            for j in range(7):
                idx = text.find(r'<td align="center">', idx)  # 从begin位置开始搜索
                end = text.find(r'</td>', idx)
                temp[tempList[j]] = text[idx + 19:end].strip()
                idx = end
            temp['成绩'] = re.search(
                r'<p align="center">(.*?)&nbsp;', temp['成绩']).group(1)
            temp['考试时间'] = '666666'
            allGrade.append(temp)

        return allGrade

    # 获取不及格课程数据
    def getAllFlunkInfo(self,model = 1):
        '''
        1为返回2个返回值 所有挂科次数（包括挂科已过）
        2为返回3个返回值 挂科数据（只包括现在还挂的科目）
        '''
        r = self.ression.get(
            '%s/gradeLnAllAction.do?type=ln&oper=bjg' % Role.eduUrl)
        # 先按照及格和不及格划分
        pattern = re.compile(
            r'<table.*?class="titleTop2">(.*?)</table>', re.S)
        result = re.findall(pattern, r.text)
        # result[0] 尚不及格  result[1] 曾不及格
        if len(result) != 2:
            raise MyURPHtmlErr(r.text)
        currentFlunkHtml = result[0]
        onceFlunkHtml = result[1]
        pattern = re.compile(r'<tr class="[a-zA-Z]+.*?(<td.*?)</tr>', re.S)

        result = re.finditer(pattern, currentFlunkHtml)
        currentFlunkCount = {}
        currentFlunkGrade = []
        onceFlunkCount = {}
        # 这里可以考虑复用设置成类全局变量
        tempList = ['课程号', '课序号', '课程名', '英文课程名', '学分',
                    '课程属性', '成绩', '考试时间']
        for item in result:
            text = item.group(1)
            idx = 0
            temp = dict.fromkeys(tempList)
            for j in range(8):
                idx = text.find(r'<td align="center">', idx)  # 从begin位置开始搜索
                end = text.find(r'</td>', idx)
                temp[tempList[j]] = text[idx + 19:end].strip()
                idx = end

            temp['成绩'] = re.match(r'<p align="left">(.*?)&nbsp;',temp['成绩']).group(1)
            currentFlunkGrade.append(temp)
            if temp['课程号'] in currentFlunkCount:
                # 课程存在
                currentFlunkCount[temp['课程号']] = currentFlunkCount[temp['课程号']] + 1
            else:
                currentFlunkCount[temp['课程号']] = 1

        result = re.finditer(pattern, onceFlunkHtml)
        for item in result:
            text = item.group(1)
            idx = 0
            temp = dict.fromkeys(tempList)
            for j in range(8):
                idx = text.find(r'<td align="center">', idx)  # 从begin位置开始搜索
                end = text.find(r'</td>', idx)
                temp[j] = text[idx + 19:end].strip()
                idx = end
            if temp[0] in onceFlunkCount:
                # 课程不存在
                onceFlunkCount[temp[0]] = onceFlunkCount[temp[0]] + 1
            else:
                onceFlunkCount[temp[0]] = 1
        if model == 1:
            return currentFlunkCount, onceFlunkCount
        else:
            return currentFlunkCount, onceFlunkCount,currentFlunkGrade

    # 获取本学期成绩
    def getNowSemesterGrade(self):
        r = self.ression.get(
            "%s/bxqcjcxAction.do?mytype=bxqcj" % Role.eduUrl)

        pattern = re.compile(r'<tr class="[a-zA-Z]+.*?(<td.*?)</tr>', re.S)
        result = re.finditer(pattern, r.text)
        # 未出成绩  已出成绩
        wccj, yccj,flunkList = [], [], []
        temp = None

        for i in result:
            text = i.group(1)
            idx = 0
            tempList = ['课程号', '课序号', '课程名', '英文课程名', '学分',
                        '课程属性', '课程最高分', '课程最低分', '课程平均分', '成绩', '名次']
            temp = dict.fromkeys(tempList)
            for j in range(11):
                idx = text.find(r'<td align="center">', idx)  # 从begin位置开始搜索
                end = text.find(r'</td>', idx)
                temp[tempList[j]] = text[idx + 19:end].strip()
                idx = end
            temp['考试时间'] = '666666'
            if temp['成绩'] == '':
                wccj.append(temp)
                continue
            elif re.match('[0-5][0-9]|不及格', temp['成绩']) != None:
                flunkList.append(temp)
            yccj.append(temp)
            #    jgcj.append(temp)
        if temp != None:
            return wccj,flunkList,yccj
        elif r.text.find('提示') != -1:
            raise MyURPHtmlErr(r.text)
        return wccj,flunkList,yccj



def firstEntering(role, dbHepler):
    URPCrawlerDAO.StudentsInfoDao(role, dbHepler).insert()
    # 执行事物提交
    dbHepler.commit()
    URPCrawlerDAO.CourseInfoDao(role, dbHepler).insert()
    URPCrawlerDAO.StudentsGradeDao(role, dbHepler).allGradeInsert()
    # 执行事物提交
    dbHepler.commit()

def currentEntering(role, dbHepler):
    URPCrawlerDAO.StudentsGradeDao(role, dbHepler).nowSemesterInsert()
    dbHepler.commit()


def updateStudentInfo(role, dbHepler):
    URPCrawlerDAO.StudentsInfoDao(role, dbHepler).insert()
    # 执行事物提交
    dbHepler.commit()

class processDataToNET (threading.Thread):
    def __init__(self, threadID,roleInfoQueue):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self._RoleInfoQueue = roleInfoQueue

    def run(self):
        index = 1
        session = requests.Session()
        while True:
            time.sleep(0.05)
            role = self._RoleInfoQueue.get()
            #try:
            #    allGrade = role._AllGrade
            #    if allGrade is not None:
            #        NET.pushAllGrade(session,role.userId,allGrade)
            #        print('%d : %s allGrade pust success!' % (index,role.userId))
            #except Exception as e:
            #    print('%d : %s allGrade pust Exception!' % (index,role.userId))
            try:
                flunkGrade = role._CurrentFlunkGrade
                if flunkGrade is not None:
                    NET.pushFlunkGrade(session,role.userId,flunkGrade)
                elif role._NowSemesterFlunkGrade is not None:
                    print('在不可能出错的地方居然出错了，，，卧槽卧槽不可能！')
                    print('%d : %s flunkGrade pust success!' % (index,role.userId))
            except Exception as e:
                print('%d : %s flunkGrade pust Exception!' % (index,role.userId))
            try:
                nowSemesterGrade = role._NowSemesterGrade
                if nowSemesterGrade is not None:
                    NET.pushNowSemesterGrade(session,role.userId,nowSemesterGrade)
                    print('%d : %s nowSemesterGrade pust success!' % (index,role.userId))
            except Exception as e:
                print('%d : %s nowSemesterGrade pust Exception!' % (index,role.userId))
            try:
                evaluateInfo = role._ERRORList
                NET.pushEvaluateInfo(session,role.userId,evaluateInfo[0])
                print('%d : %s evaluateInfo pust success!' % (index,role.userId))
            except Exception as e:
                print('%d : %s evaluateInfo Exception!' % (index,role.userId))
            
            index = index + 1

class processDataToSqlite (threading.Thread):
    '''
    处理数据存入Sqllite
    '''
    def __init__(self, threadID,roleInfoQueue,dbHepler):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self._DBHepler = dbHepler
        self._RoleInfoQueue = roleInfoQueue

    def run(self):
        index = 1
        while True:
            time.sleep(0.05)
            role = self._RoleInfoQueue.get()
            try:
                # 跳过账号登陆不成功的
                if role._ERRORList[0] == 0:
                    continue
                # 首次录入
                firstEntering(role,dbHepler)
                # 查询本学期成绩 并更新数据库
                currentEntering(role, dbHepler)
                # 更新学生个人信息
                # updateStudentInfo(role, dbHepler)
                print('%d : %s firstEntering Success!' % (index,role.userId))
            except Exception as e:
                print('traceback.print_exc():')
                traceback.print_exc()
                print('%d : %s firstEntering Exception!' % (index,role.userId))
            
            index = index + 1

class processCrawlURPData (threading.Thread):
    '''
    URP数据爬取线程
    '''
    def __init__(self, threadID,UPQueue,RoleInfoQueue,roleInfoSqlliteQueue):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self._UPQueue = UPQueue
        self._RoleInfoQueue = RoleInfoQueue
        self._RoleInfoSqlliteQueue = roleInfoSqlliteQueue
    def run(self):
        index = 1
        while True:
            time.sleep(0.05)
            UPQueue = self._UPQueue.get()
            try:
                time_start = time.time() * 1000
                userId,passWd = UPQueue[0],UPQueue[1]
                if passWd == None:
                    passWd = userId
                role = Role(userId, passWd)
                role.semester = '2016-2017-2'
                role.login()
                role._CourseList = role.getCourse()
                role._XJInfo = role.getXJInfo()
                role._AllGrade = role.getAllGrade()
                # 未出和本学期不及格和已出
                notYetGrade,role._NowSemesterFlunkGrade,role._NowSemesterGrade = role.getNowSemesterGrade()
                currentFlunkCount, onceFlunkCount,currentFlunkGrade = role.getAllFlunkInfo(model = 2)
                role._CurrentFlunkCount = currentFlunkCount
                role._OnceFlunkCount = onceFlunkCount
                role._CurrentFlunkGrade = currentFlunkGrade

                status = '学号：%s 爬取成功!' % userId
                # 加入错误队列
                role._ERRORList = [1,status]
            except Exception as e:
                status = '学号: %s 爬取失败! 原因:%s' % (userId, e.message)
                # 加入到数据队列
                role._ERRORList = [0,status]
            finally:
                self._RoleInfoQueue.put(role)
                self._RoleInfoSqlliteQueue.put(role)
                time_end = time.time() * 1000
                print("%s ,耗时 %s ms" % (status, time_end - time_start))
        else:
            pass

if __name__ == "__main__":
    # 教务系统URL
    Role.eduUrl = 'http://192.168.4.106'
    dbHepler = DBHelper.Sqlite3Helper('database\demodatabase.db')
    dbHepler.open(check_same_thread=False)
    # 从数据库里获得用户密码信息
    # tupleList = URPCrawlerDAO.StudentsGradeDao.getallStudentAccounsInfo(dbHepler)
    # tupleLen = len(tupleList)
    # index = 0
    # 角色队列1
    roleInfoQueue = queue.Queue()
    # 角色队列2
    roleInfoSqlliteQueue = queue.Queue()
    # 用户密码元组队列
    UPQueue = queue.Queue()
    # 从微信服务端获取用户密码信息
    UPList = NET.getAllIdAndPwd()
    for item in UPList:
        UPQueue.put(item)
        
    # 微信服务端接口操作线程
    # objProcessDataToNETThread = []
    # for i in range(1,2):
    #   t = processDataToNET('processNET-%d'%i,roleInfoQueue)
    #   t.daemon = True
    #   t.start()
    #   objProcessDataToNETThread.append(t)
    # 本机sqllite 数据操作
    objprocessDataToSqliteThread = processDataToSqlite('processSQLlite',roleInfoSqlliteQueue,dbHepler)
    objprocessDataToSqliteThread.daemon = True
    objprocessDataToSqliteThread.start()
    # 爬取教务系统数据线程
    objProcessCrawlURPDataThread = []
    for i in range(1,6):
        t = processCrawlURPData('processCrawl-%d'%i,UPQueue,roleInfoQueue,roleInfoSqlliteQueue)
        t.daemon = True
        t.start()
        objProcessCrawlURPDataThread.append(t)
    while True:
        time.sleep(0.07)
        pass