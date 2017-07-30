#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-07-05 16:53:19
# @Author  : mayongze (1014057907@qq.com)
# @Link    : https://github.com/mayongze
# @Version : 1.1.1.20170705

import re
import DBHelper
import traceback

class MyError(Exception):

    def __init__(self, errMessage):
        Exception.__init__(self)
        self.message = errMessage


class CourseInfoDao(object):
    """docstring for CourseInfo"""

    def __init__(self, role, dbHelper):
        self._Role = role
        self._DBHelper = dbHelper

    def insert(self, corrector=False):
        """
        插入课程操作
        有校正模式为True的时候,先查询成绩,在对比数据库中数据,对课程表进行校对
        防止因为各种原因导致的单个班级课程没爬取完造成的课程表信息缺失
        当校正模式为Flase的时候,先查询是否存在当前班级课程表,不存在抓取插入,存在不查询
        """
        if corrector:
            pass
        else:
            if not self.CourseIsExist():
                # 不存在插入
                courseList = self._Role.CourseList
                # weektype 1 普通 2单周 3 双周 4 普通但是中间停课 5 普通+单周 6 双周+普通
                for course in courseList:
                    # 判断周次
                    tmp = course['周次']
                    if tmp.strip() == '':
                        continue
                    stopto = 0
                    stopfrom = 0
                    if tmp.find('-') != -1:
                        if tmp.count('-') > 1:
                            weektype = 4
                            s = re.search(r'(\d+)-(\d+),(\d+)-(\d+)', tmp)
                            weekfrom = s.group(1)
                            stopfrom = int(s.group(2)) + 1
                            stopto = int(s.group(3)) - 1.8
                            weekto = s.group(4)

                        elif tmp.find(',') != -1:
                            s = re.search(r'(\d+),(?:(\d+),)+(\d+)-(\d+)', tmp)
                            weekfrom = s.group(1)
                            weekto = s.group(2)
                            stopfrom = s.group(3)
                            stopto = s.group(4)
                            if int(weekfrom) % 2 == 0:
                                weektype = 6
                            else:
                                weektype = 5
                        else:
                            s = re.search(r'(\d+)-(\d+)', tmp)
                            weekfrom = s.group(1)
                            weekto = s.group(2)
                            weektype = 1
                    elif tmp.find(',') == -1:
                        weektype = 1
                        s = re.search(r'\d+', tmp)
                        weekfrom = s.group()
                        weekto = s.group()
                    else:
                        s = re.search(r'(\d+)(?:,(\d+))+', tmp)
                        weekfrom = s.group(1)
                        weekto = s.group(2)
                        if int(weekfrom) % 2 == 0:
                            weektype = 3
                        else:
                            weektype = 2
                    # 处理课程 查询当前课程是否在课程信息表里,不存在插入
                    self.CourseIdProcess(course, isUpGrade=False)
                    flag = self._DBHelper.fetchone(
                        "select * from main.course_time where courseid='%s' and bld='%s' and place='%s' and weekfrom=%s and weekto=%s and stopfrom=%s and stopto=%s and weektype=%s and day=%s and lesson=%s and teacher='%s'" % (course['课程号'], course['教学楼'], course['教室'], weekfrom, weekto, stopfrom, stopto, weektype, course['星期'], course['节次'], course['节数']))
                    if not flag:
                        self._DBHelper.execute(
                            "insert into main.course_time values(null,%s,%s,%s,%s,%s,%s,%s,'%s','%s','%s','%s','%s','%s')" % (weekfrom, weekto, stopfrom, stopto, weektype, course['星期'], course['节次'], course['课程号'], course['课序号'], course['教师'], course['校区'], course['教学楼'], course['教室']), commit_at_once=False)
                        tid = self._DBHelper.fetchone(
                            "select last_insert_rowid()")
                    else:
                        tid = flag

                    self._DBHelper.execute(
                        "insert into main.syllabus values(null,'%s',%s,'%s')" % (self._Role.XJInfo["班级"], tid[0], self._Role.semester), commit_at_once=False)

    def CourseIsExist(self):
        """
        查询是否存在当前班级课程,存在为True 不存在返回False
        """
        if self._Role.XJInfo["班级"] == None:
            # 这种操作是否需要用单例模式 需要考虑
            self._Role.XJInfo["班级"] = StudentsInfoDao(
                self._Role, self._DBHelper).getStudentClass()
            if self._Role.XJInfo["班级"] is None:
                raise MyError(
                    "数据库班级为None.插入course_time 操作 学号为: %s" % self._Role.userId)
        flag = self._DBHelper.fetchone(
            "select * from main.syllabus where s_class='%s' and semester='%s'" % (self._Role.XJInfo["班级"], self._Role.semester))
        if flag:
            return True
        else:
            return False

    def CourseIdProcess(self, course, isUpGrade=False):
        """
        查询课程号是否在课程信息里面 不能存在则插入
        这里函数重复，等字段统一后可以使用 courseInfoDao = CourseInfoDao(self._Role,self._DBHelper)
        isUpGrade 为True 更新课程 最高分最低分平均分
        """
        strSql = "select * from main.course where c_no='%s'" % (course['课程号'])
        if isUpGrade == True:
            strSql = strSql + (" and c_highest_score='%s' and c_lowest_score='%s' and c_average_score='%s'" %
                               (course['课程最高分'], course['课程最低分'], course['课程平均分']))

        flag = self._DBHelper.fetchone(strSql)
        if flag:
            return True
        else:
            if isUpGrade == True:
                # 这里可以直接更新,因为能查到本学期成绩的一定爬过课表,c_no肯定存在,为了保险还是用 REPLACE
                strSql = "REPLACE into main.course(c_no,c_name,c_credit,c_property,c_highest_score,c_lowest_score,c_average_score) values('%s','%s','%s','%s','%s','%s','%s')" % (
                    course['课程号'], course['课程名'], course['学分'], course['课程属性'], course['课程最高分'], course['课程最低分'], course['课程平均分'])
            else:
                strSql = "insert into main.course(c_no,c_name,c_credit,c_property) values('%s','%s','%s','%s')" % (
                    course['课程号'], course['课程名'], course['学分'], course['课程属性'])
            self._DBHelper.execute(strSql, commit_at_once=False)


class StudentsInfoDao(object):
    """学籍信息数据访问类"""

    def __init__(self, role, dbHelper):
        self._Role = role
        self._DBHelper = dbHelper

    def loadJiGuanDic(self):
        self._Province = {'11':'北京', '12':'天津', '13':'河北', '14':'山西', '15':'内蒙古', '21':'辽宁', '22':'吉林', '23':'黑龙江', '31':'上海', '32':'江苏', '33':'浙江', '34':'安徽', '35':'福建', '36':'江西', '37':'山东', '41':'河南', '42':'湖北', '43':'湖南', '44':'广东', '45':'广西', '46':'海南', '50':'重庆', '51':'四川', '52':'贵州', '53':'云南', '54':'西藏', '61':'陕西', '62':'甘肃', '63':'青海', '64':'宁夏', '65':'新疆', '71':'台湾', '81':'香港', '82':'澳门'}

    def insert(self):
        """
        插入学生个人信息
        """
        # 判断学生信息是否在数据库里面
        _xjinfo = self._Role.XJInfo
        # 为None就返回
        if not _xjinfo:
            return
        sInfo = self.getStudentInfoBySno(self._Role.userId)
        if not sInfo:
            self._DBHelper.execute(
                "insert INTO main.students(sno,s_passwd,s_name,s_sex,s_sfz,s_birth,s_addr,s_major,s_depatment,s_class,s_nemtgrade,s_ethnicity,s_highschool,s_politicalstatus,s_admissiondate,s_education,s_status,s_nemtid,s_recorddate) values (%s,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',%s,'%s','%s','%s',date('now'))" % (_xjinfo['学号'],self._Role.passWd,_xjinfo['姓名'], _xjinfo['性别'], _xjinfo['身份证号'], _xjinfo['出生日期'], _xjinfo['籍贯'], _xjinfo['专业'], _xjinfo['系所'], _xjinfo['班级'], _xjinfo['高考总分'], _xjinfo['民族'], _xjinfo['毕业中学'], _xjinfo['政治面貌'], _xjinfo['入学日期'], _xjinfo['培养层次'], _xjinfo['学籍状态'], _xjinfo['高考考生号']), commit_at_once=False)
        elif sInfo[14] == None:
            # 如果录入日期为0则需要更新数据
            self._DBHelper.execute(
                "UPDATE main.students SET s_passwd='%s',s_name='%s',s_sex='%s',s_sfz='%s',s_birth='%s',s_addr='%s',s_major='%s',s_depatment='%s',s_class='%s',s_nemtgrade='%s',s_ethnicity='%s',s_highschool='%s',s_politicalstatus='%s',s_admissiondate=%s,s_education='%s',s_status='%s',s_recorddate=date('now'),s_nemtid='%s' WHERE sno=%s" % (self._Role.passWd, _xjinfo['姓名'], _xjinfo['性别'], _xjinfo['身份证号'], _xjinfo['出生日期'], _xjinfo['籍贯'], _xjinfo['专业'], _xjinfo['系所'], _xjinfo['班级'], _xjinfo['高考总分'], _xjinfo['民族'], _xjinfo['毕业中学'], _xjinfo['政治面貌'], _xjinfo['入学日期'], _xjinfo['培养层次'], _xjinfo['学籍状态'], _xjinfo['高考考生号'], self._Role.userId), commit_at_once=False)

    def StudentIsExist(self, sno):
        """
        查询是否存在当前个人学号信息,存在为True 不存在返回False
        """
        flag = self._DBHelper.fetchone(
            "select * from main.students where sno=%s" % sno)
        if flag:
            return True
        else:
            return False

    def getStudentInfoBySno(self, sno):
        """
        根据学号查询当前个人信息
        """
        fetch = self._DBHelper.fetchone(
            "select * from main.students where sno=%s" % sno)
        return fetch

    def getStudentClass(self):
        """
        从数据库获取学生班级信息
        """
        flag = self._DBHelper.fetchone(
            "select s_class from main.students where sno=%s" % self._Role.userId)
        if not flag:
            return None
        else:
            return flag[0]


class StudentsGradeDao(object):
    """学生成绩数据访问类"""


    def __init__(self, role, dbHelper):
        self._Role = role
        self._DBHelper = dbHelper

    def getallStudentAccounsInfo(dbHelper):
        """
        此处为静态方法
        获取全部学生的账号密码信息
        """
        slist = dbHelper.fetchall("select sno,s_passwd from main.students")
        return slist

    def allGradeInsert(self):
        """
        全部成绩插入
        首先判断课程是否在Course 表里 不存在插入 
        """
        # 这里还需要把不及格次数信息统计到数据库
        # 可以在Role 增加函数获取不及格信息(尚不及格,曾不及格)采用字典返回 key为课程号 value为次数
        # 这里进行尚不及格和曾不及格的合并
        allGrade = self._Role.AllGrade
        currentFlunkCount = self._Role.CurrentFlunkCount
        onceFlunkCount = self._Role.OnceFlunkCount
        currentFlunkCount.update(onceFlunkCount)

        for grade in allGrade:
            # 这里考虑单例类
            CourseInfoDao(self._Role, self._DBHelper).CourseIdProcess(
                grade, isUpGrade=False)
            count = 0
            if grade['课程号'] in currentFlunkCount:
                count = currentFlunkCount[grade['课程号']]
            self._DBHelper.execute(
                "REPLACE INTO main.grade (sno,cno,grade,cnum,flunkcount) values(%s,'%s','%s','%s',%s)" % (
                    self._Role.userId, grade['课程号'], grade['成绩'], grade['课序号'], count), commit_at_once=False)


    def nowSemesterInsert(self):
        """
        本学期成绩插入
        更新课程 详细信息
        """
        # notYetGrade 未出
        nowGrade = self._Role.NowSemesterGrade
        flunkList = self._Role.NowSemesterFlunkGrade
        for grade in nowGrade:
            # 本学期可以更新课程最高分 平均分
            # 这里考虑单例类
            CourseInfoDao(self._Role, self._DBHelper).CourseIdProcess(
                grade, isUpGrade=True)
            flunk = len(flunkList) != 0
            # 这里为了查询到不及格次数数据 不用replace 改用先查询后更新
            result = self._DBHelper.fetchone(
                "select * from main.grade where sno=%s and cno='%s'" % (self._Role.userId, grade['课程号']))
            if not result:
                strSql = "INSERT INTO main.grade(sno,cno,grade,rank,semester,flunkcount) VALUES(%s,'%s','%s','%s','%s',%s)" % (
                    self._Role.userId, grade['课程号'], grade['成绩'], grade['名次'], self._Role.semester, int(flunk))
            else:

                if result[2] == grade['课序号']:
                    # 课程和Id存在 此时考虑是否是重复爬取 课序号相等且学期相同肯定是重复爬取了
                    if result[5] == self._Role.semester:
                        return True
                    '''
                    如果课序号相同 代表本学期已出成绩在事先在全部成绩里查到了,
                    这里仅把剩余数据不全即可，不用考虑不及格次数字段的更新,
                    此时学期字段为空需要更新排名情况以及学期信息
                    '''
                    strSql = "UPDATE main.grade SET rank='%s',semester='%s' WHERE sno=%s and cno='%s'" % (
                        grade['名次'], self._Role.semester, self._Role.userId, grade['课程号'])
                else:
                    # 此时一定为补考 而且是成绩更新 之前未出的科目 需要判断是否挂科
                    if flunk == False:
                        strSql = "UPDATE main.grade SET grade='%s',rank='%s',semester='%s' WHERE sno=%s and cno='%s'" % (
                            grade['成绩'], grade['名次'], self._Role.semester, self._Role.userId, grade['课程号'])
                    else:
                        #tmp = int(result[6]) + 1
                        #由于是全部成绩和当前成绩一起查的这里查完改回去
                        tmp = int(result[6])
                        strSql = "UPDATE main.grade SET grade='%s',rank='%s',semester='%s',flunkcount=%s WHERE sno=%s and cno='%s'" % (
                            grade['成绩'], grade['名次'], self._Role.semester, tmp, self._Role.userId, grade['课程号'])
            self._DBHelper.execute(strSql, commit_at_once=False)

    def getNowSemesterGrade(self,courseName,semester):
        '''
        获取本学期学生成绩
        '''
        # strSql = "select sno,grade from main.grade,main.course where grade.cno = course.c_no and course.c_name='%s' and grade.semester = '%s' and grade.sno < 158396 and grade.sno > 158133 ORDER BY grade.sno ASC" % (courseName, semester)
        strSql = "select grade from main.grade,main.course where grade.cno = course.c_no and course.c_name='%s' and grade.semester = '%s' ORDER BY grade.sno ASC" % (courseName, semester)
        result = self._DBHelper.fetchall(strSql)
        return result

sqlite3Obj = None

def endCommit(dbHepler = None):
    if not dbHepler:
        dbHepler = sqlite3Obj
    dbHepler.commit()

sqliteCount = 0
def firstEntering(role, dbHepler = None):
    '''
    首次录入
    '''
    global sqliteCount
    if not dbHepler:
        dbHepler = sqlite3Obj
    sqliteCount = sqliteCount + 1
    if sqliteCount == 500:
        sqliteCount = 0
        dbHepler.commit()
    StudentsInfoDao(role, dbHepler).insert()
    # 执行事物提交
    # dbHepler.commit()
    CourseInfoDao(role, dbHepler).insert()
    StudentsGradeDao(role, dbHepler).allGradeInsert()
    StudentsGradeDao(role, dbHepler).nowSemesterInsert()
    # 执行事物提交
    # dbHepler.commit()

def currentEntering(role, dbHepler = None):
    '''
    查询本学期成绩 并更新数据库
    '''
    if not dbHepler:
        dbHepler = sqlite3Obj
    StudentsGradeDao(role, dbHepler).nowSemesterInsert()
    dbHepler.commit()


def updateStudentInfo(role, dbHepler = None):
    '''
    更新学生个人信息
    '''
    if not dbHepler:
        dbHepler = sqlite3Obj
    StudentsInfoDao(role, dbHepler).insert()
    # 执行事物提交
    dbHepler.commit()

def process(dataFilePath,logfilename = 'sqliteDataProcess.log'):
    import log
    DBlog = log.set_logger(filename = logfilename, isOnlyFile = False)
    DBlog.debug('sqlite start！')
    global sqlite3Obj
    sqlite3Obj = DBHelper.Sqlite3Helper(dataFilePath)
    sqlite3Obj.open(check_same_thread=False)
    while True:
        role,index = yield
        if isinstance(role, str):
            return
        try:   
            # 跳过账号登陆不成功的
            if role.ERRORList[0] != 0:
                # 首次录入
                firstEntering(role, sqlite3Obj)
                # 查询本学期成绩 并更新数据库
                # currentEntering(role, sqlite3Obj)
                # 更新学生个人信息
                # updateStudentInfo(role, sqlite3Obj)
                DBlog.info('%d : %s firstEntering Success!' % (index, role.userId))
        except Exception as e:
            DBlog.error('%d : %s firstEntering Exception!\n -- %s' % (index,role.userId, traceback.format_exc()))
        else:
            pass
        finally:
            pass
        


def main():
    """
    主函数
    """
    pass

if __name__ == '__main__':
    main()
