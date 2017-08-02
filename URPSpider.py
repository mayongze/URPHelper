#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-07-29 16:53:19
# @Author  : mayongze (1014057907@qq.com)
# @Link    : https://github.com/mayongze
# @Version : 2.1.1.20170730

import os
import random
import captcha
import asyncio  
import aiohttp
# import uvloop
import time
import re
import copy
import traceback
import URPPipelines
from multiprocessing import Process, Manager, Pool
import NETinterface as NET
import URPCrawlerDAO
import userapiconfig

class URPSpider(object):
    # 初始化
    def __init__(self, loop=None, queue=None, spiderlog = None):
        self.loop = loop
        self.queue = queue
        # 限制最高5个协程工作
        self.sem = asyncio.Semaphore(16)
        # 负载情况查询 6个
        self.loadInfo = [0,0,0,0,0,0,0]
        # 日志文件
        self.Spiderlog = spiderlog 

    # 日志封装防止非法调用 暂时无用
    def log(self,lev,message):
        if self.Spiderlog is None:
            return


    async def login(self, role):
        # 限制同时运行的协数
        look = await self.sem
        session = role.session
        userId = role.userId
        passWd = role.passWd
        try:
            while True:
                self.loadInfo[0] = self.loadInfo[0] + 1
                async with session.get("http://192.168.4.106/validateCodeAction.do?random=%f" % random.random()) as r:
                    stream = await r.read()
                    code = captcha.getCaptcha(stream,isPrint = False)

                payload = {'zjh1': '',
                       'tips': '',
                       'lx': '',
                       'evalue': '',
                       'eflag': '',
                       'fs': '',
                       'dzslh': '',
                       'zjh': userId,
                       'mm': passWd,
                       'v_yzm': code}
                async with session.post("http://192.168.4.106/loginAction.do",data=payload) as r:
                    html = await r.text()
                self.loadInfo[0] = self.loadInfo[0] - 1
                if html.find('你输入的验证码错误，请您重新输入！') != -1:
                    # print('验证码错误!')
                    self.Spiderlog.warning('%s -- 验证码错误!' % userId)
                else:
                    break
            if (html.find('学分制综合教务') == -1):
                raise MyURPHtmlErr(html)
            else:
                # print('%s - 登录成功!' % userId)
                self.Spiderlog.info('%s - 登录成功!' % userId)
            

            self.loadInfo[1] = self.loadInfo[1] + 1
            # 获取课程表
            async with session.get("http://192.168.4.106/xkAction.do?actionType=6") as r:
                html = await r.text()
            self.loadInfo[1] = self.loadInfo[1] - 1
            # 课程列表
            role.CourseList = self.parseCourse(html)


            self.loadInfo[2] = self.loadInfo[2] + 1
            # 获取学籍信息
            async with session.get("http://192.168.4.106/xjInfoAction.do?oper=xjxx") as r:
                html = await r.text()
            self.loadInfo[2] = self.loadInfo[2] - 1
            # 学籍信息
            role.XJInfo = self.parseXueJiInfo(html)
            # self.dClass = xjinfo['班级']

            self.loadInfo[3] = self.loadInfo[3] + 1
            # 获取全部成绩
            async with session.get("http://192.168.4.106/gradeLnAllAction.do?type=ln&oper=sxinfo&lnsxdm=001") as r:
                html = await r.text()
            self.loadInfo[3] = self.loadInfo[3] - 1
            role.AllGrade = self.parseAllGrade(html)

            self.loadInfo[4] = self.loadInfo[4] + 1
            # 获取本学期成绩
            async with session.get("http://192.168.4.106/bxqcjcxAction.do?mytype=bxqcj") as r:
                html = await r.text()
            self.loadInfo[4] = self.loadInfo[4] - 1
            notYetGrade,role.NowSemesterFlunkGrade,role.NowSemesterGrade = self.parseNowSemesterGrade(html)

            self.loadInfo[5] = self.loadInfo[5] + 1
            # 获取不及格课程数据
            async with session.get("http://192.168.4.106/gradeLnAllAction.do?type=ln&oper=bjg") as r:
                html = await r.text()
            self.loadInfo[5] = self.loadInfo[5] - 1
            role.CurrentFlunkCount, role.OnceFlunkCount,role.CurrentFlunkGrade = self.parseAllFlunkInfo(html,model = 2)

            self.loadInfo[6] = self.loadInfo[6] + 1
            # 退出账号
            async with session.post("http://192.168.4.106/logout.do") as r:
                await r.read()
            self.loadInfo[6] = self.loadInfo[6] - 1
        except MyURPHtmlErr as e:
            status = '学号: %s 爬取失败! 原因:%s' % (userId, e.message)
            role.ERRORList = [0,status]
            # print(status)
            self.Spiderlog.error(status)
        except Exception as e:
            # 这里为意料之外的错误
            status = '学号: %s 爬取失败! 原因:\n%s' % (userId, traceback.format_exc())
            role.ERRORList = [0,status]
            # print(status)
            self.Spiderlog.error(status)
        else:
            # 当没有错误发生时
            status = '学号：%s 爬取成功!' % userId
            # print(status)
            self.Spiderlog.info(status)
            role.ERRORList = [1,status]

        finally:
            # self.queue.put(role)
            self.Spiderlog.info(self.loadInfo)
            look.__exit__()
            session.close()
            role.session = None
            self.queue.put(role)


    # 解析课程信息
    def parseCourse(self,html):

        pattern = re.compile(r'<tr class=.*?</tr>', re.S)

        # 这里用数组不用迭代器了
        result = re.findall(pattern, html)

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
  
    # 解析学籍信息
    def parseXueJiInfo(self,html):
        pattern = re.compile(
            r'<td class="fieldName" width="180">(.*?):&nbsp.*?">(.*?)</td>', re.S)
        result = re.finditer(pattern, html)
        xjinfo = {}
        for i in result:
            key = i.group(1).strip()
            value = i.group(2).strip()
            xjinfo[key] = value
        return xjinfo

    # 解析全部成绩
    def parseAllGrade(self,html):
        pattern = re.compile(r'<tr class="[a-zA-Z]+.*?(<td.*?)</tr>', re.S)
        result = re.finditer(pattern, html)
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

    # 解析本学期成绩
    def parseNowSemesterGrade(self,html):
        pattern = re.compile(r'<tr class="[a-zA-Z]+.*?(<td.*?)</tr>', re.S)
        result = re.finditer(pattern, html)
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
        elif html.find('提示') != -1:
            raise MyURPHtmlErr(html)
        return wccj,flunkList,yccj

    # 解析不及格成绩
    def parseAllFlunkInfo(self,html,model = 1):
        '''
        1为返回2个返回值 所有挂科次数（包括挂科已过）
        2为返回3个返回值 挂科数据（只包括现在还挂的科目）
        '''
        # 先按照及格和不及格划分
        pattern = re.compile(
            r'<table.*?class="titleTop2">(.*?)</table>', re.S)
        result = re.findall(pattern, html)
        # result[0] 尚不及格  result[1] 曾不及格
        if len(result) != 2:
            raise MyURPHtmlErr(html)
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


    def run(self,dataSource = None):
        # 初始化生产者
        # 这里可以将不同类型的爬虫加入异步循环
        tasks = [self.login(item) for item in self.getRole(dataSource = dataSource)]
        # 执行协程对象
        self.loop.run_until_complete(asyncio.gather(*tasks))

    def close(self):
        self.loop.close()

    # 角色生成器
    def getRole(self,dataSource = None):
        # 从微信服务端获取用户密码信息
        if not dataSource:
            allIdPW = NET.getAllIdAndPwd()
        else:
            allIdPW = dataSource
        if "Spiderlog" in dir():
            Spiderlog.info('获取任务数据: %s 条' % len(allIdPW))
        for userId,passWd in allIdPW:
            # aiohttp 默认禁止从IP接受cookies信息 这里打开
            jar = aiohttp.CookieJar(unsafe=True)
            session = aiohttp.ClientSession(loop=self.loop,cookie_jar=jar)
            role = studenItem(userId,passWd,session)
            yield role

# 测试用例
userId = ["148253","148254","148255","148256","148257","148258"]
passWd = ["148253","148254","148255","148256","148257","148258"]
# 失败次数
autoCode = 0 
 
#            # 只在插入用户的时候才下载照片
#            self._Role.downLoadPhoto()

class studenItem(object):
    def __init__(self,userId,passWd,session):
        self.userId = userId
        self.passWd = passWd
        self.session = session
        # 课程表
        self.CourseList = None
        # 学籍
        self.XJInfo = None
        # 全部成绩
        self.AllGrade = None
        # 本学期成绩
        self.NowSemesterGrade = None
        # 本学期不及格成绩
        self.NowSemesterFlunkGrade = None
        # 现在课程不及格次数
        self.CurrentFlunkCount = None
        # 曾经课程不及次格数
        self.OnceFlunkCount = None
        # 现在不急个成绩
        self.CurrentFlunkGrade = None
        # 错误列表
        self.ERRORList = None
        # 学年
        self.semester = '2016-2017-2'

# 异常错误类
class MyURPHtmlErr(Exception):
    html = None

    def __init__(self, html):
        Exception.__init__(self)
        self.html = html
        self.message = self.htmlErrMeg()

    def htmlErrMeg(self):
        try:
            m = re.search(
            r'<td class="errorTop">.*?<font color="#990000">(.*?)</font>', self.html, re.S)
            return m.group(1)
        except Exception as e:
            return self.html


def SpiderStart(q,logfilename = 'URPSpider.log',dataSource = None,sprstatus = None):
    import log as Spiderlog
    Spiderlog.set_logger(filename = logfilename)
    # loop = uvloop.new_event_loop()
    # asyncio.set_event_loop(loop)  
    loop = asyncio.get_event_loop()
    urp = URPSpider(loop,queue = q,spiderlog = Spiderlog)
    urp.run(dataSource = dataSource)
    urp.close()
    if sprstatus is not None:
        sprstatus['Spider'] = sprstatus['Spider'] - 1
        Spiderlog.debug('任务结束! -- 当前剩余任务进程数:%s' % sprstatus['Spider'])    
        if sprstatus['Spider'] == 0:
            # 当爬虫运行数目为0的时候增加数据储存结束标示
            q.put('end')


# 列表分割
def list_of_groups(list_1, list_len):
    temp = int(len(list_1) / list_len)
    a = []
    a.append(list_1[:temp])
    temp1 = temp
    for i in range(1,list_len-1):
        a.append(list_1[temp1:temp1 + temp])
        temp1 = temp1 + temp
    else:
        a.append(list_1[temp1:])
    return a


if __name__ == '__main__':
# 需要一个用户一个session 因为要带cookies验证
# 生产者:用户名密码  消费者:登录爬取
# 生产者:爬取到的数据 消费者:数据清洗到http or SQLite
#
# 1.请求验证码 2.登录 3.错误接着请求验证码 4.成功开始请求其他数据
# 5.爬取学籍信息 6.爬取课程表信息 7.爬取已修成绩信息 8.爬取不及格成绩 9.爬取本学期成绩 10.结束
#
# 多进程任务队列

    mgr = Manager()
    q = mgr.Queue()
    # 爬虫运行状态
    sprstatus = mgr.dict()


    PROCESS_NUM = userapiconfig.SPIDER_PROCESS_NUM

    sprstatus['Spider'] = PROCESS_NUM
    userInfo = NET.getAllIdAndPwd()
    # userInfo = userInfo[:20]
    list_data =  list_of_groups(userInfo,PROCESS_NUM)
    p = Pool(processes = PROCESS_NUM + 1)

    for i in range(PROCESS_NUM):
        p.apply_async(SpiderStart, args = (q,'spiderProcess_%s.log' % i, list_data[i],sprstatus))
    p.apply_async(URPPipelines.main, args=(q, 1))

    p.close()
    p.join()
    print('进程池任务结束!')

    # 等待进程结束
    #dataProcess.join()
    # 强制结束掉因为子进程是死循环
    # dataProcess.terminate()