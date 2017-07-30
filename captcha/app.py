#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-07-22 23:05:28
# @Author  : mayongze (1014057907@qq.com)
# @Link    : https://github.com/mayongze
# @Version : $Id$

import ctypes,os,hashlib

dll = None
path = None

def init():
    global dll
    global path
    path = os.getcwd()
    dll = ctypes.windll.LoadLibrary(os.path.join(path,"captcha",'WmCode.dll'))
    os.chdir(path)
    # 创建临时目录
    dir = os.path.join(path,"captcha",'tmp')
    if not os.path.isdir(dir):
        os.mkdir(dir)
    if dll.UseUnicodeString(1,1) and dll.LoadWmFromFile(os.path.join(path,"captcha",'urlCaptcha.dat'),'mayongze') and dll.SetWmOption(7,-1) and dll.SetWmOption(4,1) and dll.SetWmOption(6,80):
        print('captcha init success!')
    else:
        print('captcha init error!')
        os._exit(0)
init()

def getCaptcha(stream,length = None,isPrint = True):
    str = ctypes.create_string_buffer(7)#创建文本缓冲区
    if length is None:
        length = len(stream)
    if(dll.GetImageFromBuffer(stream,length,str)):#使用绝对路径
        code = str.raw.decode("gbk").split('\x00')[0]
        flag = 'GetVcode Success:%s' % (code,)
        # flag = 'Success'
        # 将明显识别错误的验证码图片保存下来
        if len(code) != 4:
            imgName =os.path.join(path,"captcha","tmp") + '/%s-%s.jpg' % (code,hashlib.md5(stream).hexdigest())
            with open(imgName, 'wb') as f:
                f.write(stream)
                f.flush()
                f.close()
    else:
        flag = 'GetVcode Fail!'
    if isPrint:
        print(flag)
    return code

if __name__ == '__main__':
    pass
