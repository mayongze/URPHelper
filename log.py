#!/usr/local/python/bin
# coding=utf-8

# 日志级别
# CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET

'''实现一个简单的日志库。
 
这个模块是一个简单的封装日志模块来提供更多的
方便的界面来写日志。 日志将打印到stdout和
写入日志文件。 它提供了更灵活的方式来设置日志操作，
也很简单。 参见下面的例子：
 
示例1：使用默认设置
 
    import log
 
    log.debug('hello, world')
    log.info('hello, world')
    log.error('hello, world')
    log.critical('hello, world')
 
结果：
将所有日志消息打印到文件，并且仅打印级别较大的日志
比错误到stdout。 该日志文件位于“/tmp/xxx.log”中
名称是xxx.py。 默认的日志文件处理程序是大小轮替的，如果日志
文件的大小大于20M，那么它将被轮替。
 
示例2：使用set_logger更改设置
 
     ＃更改默认轮替操作的字节数限制大小
     log.set_logger（limit = 10240）＃10M
 
     ＃使用时间轮替的文件处理程序，每天都有不同的日志文件，看
     ＃logging.handlers.TimedRotatingFileHandler获取更多有关“何时”的帮助
     log.set_logger（when ='D'，limit = 1）
 
     ＃使用普通文件处理程序（不轮替）
     log.set_logger（backup_count = 0）
 
     ＃stdout日志级别设置为DEBUG，文件日志级别设置为INFO  默认ERROR:DEBUG
     log.set_logger（level ='DEBUG:INFO'）
 
     ＃两个日志级别设置为INFO
     log.set_logger（level ='INFO'）
 
     ＃更改默认日志文件名和日志模式
     log.set_logger（filename ='yyy.log'，mode ='w'）
 
     ＃更改默认日志格式化程序
     log.set_logger（fmt ='[％（levelname）s]％（message）s'

     #更改默认文件日志文件 相对路径log
     log.set_logger（logdir = 'log')
'''
 
__author__ = "tuantuan.lv <dangoakachan@foxmail.com>"
__status__ = "Development"
 
__all__ = ['set_logger', 'debug', 'info', 'warning', 'error',
           'critical', 'exception']
 
import os
import sys
import colorama
from colorama import Fore, Back, Style
import logging
import logging.handlers
 
colorama.init()
# Color escape string
COLOR_RED=Fore.RED#'\033[1;31m'
COLOR_GREEN=Fore.GREEN#'\033[1;32m'
COLOR_YELLOW=Fore.YELLOW#'\033[1;33m'
COLOR_BLUE=Fore.BLUE#'\033[1;34m'
COLOR_PURPLE=Fore.MAGENTA#'\033[1;35m'
COLOR_CYAN=Fore.CYAN#'\033[1;36m'
COLOR_GRAY=Fore.WHITE#'\033[1;37m'
COLOR_WHITE=Fore.WHITE#'\033[1;38m'
COLOR_RESET=Fore.RESET#'\033[1;0m'
 
# Define log color
LOG_COLORS = {
    'DEBUG': '%s',
    'INFO': COLOR_GREEN + '%s' + COLOR_RESET,
    'WARNING': COLOR_YELLOW + '%s' + COLOR_RESET,
    'ERROR': COLOR_RED + '%s' + COLOR_RESET,
    'CRITICAL': COLOR_RED + '%s' + COLOR_RESET,
    'EXCEPTION': COLOR_RED + '%s' + COLOR_RESET,
}
 
# Global logger
g_logger = None
multifile = None
 
class ColoredFormatter(logging.Formatter):
    '''A colorful formatter.'''
 
    def __init__(self, fmt = None, datefmt = None):
        logging.Formatter.__init__(self, fmt, datefmt)
 
    def format(self, record):
        level_name = record.levelname
        msg = logging.Formatter.format(self, record)
 
        return LOG_COLORS.get(level_name, '%s') % msg
 
def add_handler(cls, level, fmt, colorful, **kwargs):
    '''Add a configured handler to the global logger.'''
    global g_logger
 
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.DEBUG)
 
    handler = cls(**kwargs)
    handler.setLevel(level)
 
    if colorful:
        formatter = ColoredFormatter(fmt)
    else:
        formatter = logging.Formatter(fmt)
 
    handler.setFormatter(formatter)
    g_logger.addHandler(handler)
 
    return handler
 
def add_streamhandler(level, fmt):
    '''Add a stream handler to the global logger.'''
    return add_handler(logging.StreamHandler, level, fmt, True)
 
def getfilename(filename = None):
    if filename is None:
        filename = getattr(sys.modules['__main__'], '__file__', 'log.py')
        filename = os.path.basename(filename.replace('.py', '.log'))
    return filename

def add_filehandler(level, fmt, filename , mode, backup_count, limit, when, logdir):
    '''Add a file handler to the global logger.'''
    kwargs = {}
 
    # If the filename is not set, use the default filename
    filename = getfilename(filename)
        #dir = os.path.dirname(self.file_name)
    if not os.path.isdir(logdir):
        os.mkdir(logdir)
    filename = os.path.join(logdir, filename)
 
    kwargs['filename'] = filename
 
    # Choose the filehandler based on the passed arguments
    if backup_count == 0: # Use FileHandler
        cls = logging.FileHandler
        kwargs['mode' ] = mode
    elif when is None:  # Use RotatingFileHandler
        cls = logging.handlers.RotatingFileHandler
        kwargs['maxBytes'] = limit
        kwargs['backupCount'] = backup_count
        kwargs['mode' ] = mode
    else: # Use TimedRotatingFileHandler
        cls = logging.handlers.TimedRotatingFileHandler
        kwargs['when'] = when
        kwargs['interval'] = limit
        kwargs['backupCount'] = backup_count
 
    return add_handler(cls, level, fmt, False, **kwargs)


def init_logger(filename,isOnlyFile):
    '''Reload the global logger.
       isOnlyFile 为 None 或 True 可以接收第三方模块内置的日志信息,但是基类日志会记录所有日志
       isOnlyFile 为 False 可以在统一进程中分文件单独记录日志,但是无法记录第三方模块内置的日志信息
    '''
    global g_logger

    if not isOnlyFile:
        #多日志文件模式用日志名区分
        g_logger = logging.getLogger(getfilename(filename))
    else:
        # 这里是单文件模式
        if g_logger is None or multifile is not None:
            g_logger = logging.getLogger()
        else:
            logging.shutdown()
            g_logger.handlers = []

    
    g_logger.setLevel(logging.DEBUG)
 
def set_logger(filename = None, mode = 'a',level='ERROR:DEBUG',
               fmt = '[%(levelname)s] %(asctime)s %(message)s',
               backup_count = 5, limit = 20240 * 1024, when = None, logdir = 'log', isOnlyFile = True):
    global multifile
    if not isOnlyFile:
        multifile = isOnlyFile
    '''Configure the global logger.'''
    level = level.split(':')
 
    if len(level) == 1: # Both set to the same level
        s_level = f_level = level[0]
    else:
        s_level = level[0]  # StreamHandler log level
        f_level = level[1]  # FileHandler log level
    
    init_logger(filename,isOnlyFile)
    add_streamhandler(s_level, fmt)
    add_filehandler(f_level, fmt, filename, mode, backup_count, limit, when, logdir)
 
    # Import the common log functions for convenient
    import_log_funcs()
    return g_logger
 
def import_log_funcs():
    '''Import the common log functions from the global logger to the module.'''
    global g_logger
 
    curr_mod = sys.modules[__name__]
    log_funcs = ['debug', 'info', 'warning', 'error', 'critical',
                 'exception']
 
    for func_name in log_funcs:
        func = getattr(g_logger, func_name)
        setattr(curr_mod, func_name, func)
 
# Set a default logger
# set_logger()