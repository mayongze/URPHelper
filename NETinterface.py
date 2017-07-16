#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-07-05 16:53:19
# @Author  : mayongze (1014057907@qq.com)
# @Link    : https://github.com/mayongze
# @Version : 1.1.1.20170705

import os
import re
import requests
import userapiconfig

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

def pushEvaluateInfo(session,userId,flag):
    session.post(URL,params={'aspx':'14','xuehao':userId,'cont':flag})

def pushNowSemesterGrade(session,userId,gradeDic):
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
        session.post(params)

def pushFlunkGrade(session,userId,gradeDic):
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
        session.post(params)

def pushAllGrade(session,userId,gradeDic):
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
        session.post(params)  

def main():
    pass

if __name__ == '__main__':
    main()