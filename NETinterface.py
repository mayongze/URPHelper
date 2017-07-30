#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-07-05 16:53:19
# @Author  : mayongze (1014057907@qq.com)
# @Link    : https://github.com/mayongze
# @Version : 2.1.1.20170730

import os
import re
import requests
import aiohttp
import asyncio
import userapiconfig
import traceback
import time

URL = userapiconfig.URL
# DICKEY = ['课程号', '课程名', '学分', '考试时间', '期末成绩']

def getAllIdAndPwd():
    r = requests.get(URL,params={'aspx':'9'})
    # 去除前导字符串
    html = r.text.lstrip('ï»¿ï»¿ ')
    pattern = re.compile(
            r"xuehao:(\d+),mima:([^}]+)")
    iterUP = re.finditer(pattern,html)
    UPList = [ ("%s"%i.group(1),"%s"%i.group(2)) for i in iterUP];
    # for item in iterUP:
    #     UPList.append(("%s"%itemg.group(1),"%s"%itemg.group(2)))
    # exec("list=%s" % '[{xuehao:149068,mima:149068},{xuehao:148290,mima:zzydbk},{xuehao:148499,mima:148499},{xuehao:148394,mima:148394},{xuehao:148924,mima:148924},{xuehao:149120,mima:xbg521}]')
    # print(list)
    return UPList

# 评价状态
async def pushEvaluateInfo(session,userId,flag):
    async with session.post(URL,params={'aspx':'14','xuehao':userId,'cont':flag}) as r:
        return r.status

# 本学期成绩
async def pushNowSemesterGrade(session,userId,gradeDic):
    cont = []
    for item in gradeDic:
        dic = {}
        dic['课程号'] = item['课程号']
        dic['课程名'] = item['课程名']
        dic['学分'] = item['学分']
        dic['考试时间'] = item['考试时间']
        dic['期末成绩'] = item['成绩']
        cont.append(dic)
    if len(cont) != 0:
        params = URL + "?aspx=13&xuehao={0}&cont={1}".format(userId,str(cont).replace(r"'",r'"'))
        async with session.post(params) as r:
            return r.status

# 不及格成绩
async def pushFlunkGrade(session,userId,gradeDic):
    cont = []
    for item in gradeDic:
        dic = {}
        dic['课程号'] = item['课程号']
        dic['课程名'] = item['课程名']
        dic['学分'] = item['学分']
        dic['考试时间'] = item['考试时间']
        dic['期末成绩'] = item['成绩']
        cont.append(dic)
    if len(cont) != 0:
        params = URL + "?aspx=11&xuehao={0}&cont={1}".format(userId,str(cont).replace(r"'",r'"'))  
        async with session.post(params) as r:
            return r.status
    else:
        return 0

# 全部成绩
async def pushAllGrade(session,userId,gradeDic):
    cont = []
    for item in gradeDic:
        dic = {}
        dic['课程号'] = item['课程号']
        dic['课程名'] = item['课程名']
        dic['学分'] = item['学分']
        dic['考试时间'] = item['考试时间']
        dic['期末成绩'] = item['成绩']
        cont.append(dic)
    if len(cont) != 0:
        params = URL + "?aspx=12&xuehao={0}&cont={1}".format(userId,str(cont).replace(r"'",r'"'))
        async with session.post(params) as r:
            return r.status


async def push(session, role, log):
    try:
        #allGrade = role._AllGrade
        #if allGrade is not None:
        #    pushAllGrade(session,role.userId,allGrade)
        flunkGrade = role.CurrentFlunkGrade
        if flunkGrade is not None:
            status = await pushFlunkGrade(session,role.userId,flunkGrade)
            if status == 200 or status == 0:
                log.info(' %s -- 不及格成绩推送成功! status: %s' % (role.userId,status))
            else:
                log.info(' %s -- 不及格成绩推送失败! status: %s data= %s' % (role.userId,status,flunkGrade))
        nowSemesterGrade = role.NowSemesterGrade
        if nowSemesterGrade is not None:
            status = await pushNowSemesterGrade(session,role.userId,nowSemesterGrade)
            if status == 200 or status == 0:
                log.info(' %s -- 本学期成绩推送成功! status: %s' % (role.userId,status))
            else:
                log.info(' %s -- 本学期成绩推送失败! status: %s data= %s' % (role.userId,status,nowSemesterGrade))
        evaluateInfo = role.ERRORList
        status = await pushEvaluateInfo(session,role.userId,evaluateInfo[0])
        if status == 200 or status == 0:
            log.info(' %s -- 评教状态推送成功! status: %s' % (role.userId,status))
        else:
            log.info(' %s -- 评教状态推送失败! status: %s' % (role.userId,status))
    except Exception as e:
        log.error("未知错误 %s" % traceback.format_exc())


def main():
    loop = asyncio.get_event_loop()
    session = aiohttp.ClientSession(loop=loop)
    tasks = [pushEvaluateInfo(session,'148253',1),pushEvaluateInfo(session,'148254',1)]
    #tasks = [self.login(item) for item in self.getRole(dataSource = dataSource)]
    # 执行协程对象
    loop.run_until_complete(asyncio.gather(*tasks))
    session.close()

if __name__ == '__main__':
    main()