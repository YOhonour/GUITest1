# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QHeaderView, QAbstractItemView, QTableWidgetItem

from UI import Ui_MainWindow
import sys
import xlwt
from src.SpiderTest import *


class MainUI(Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.mianTextURL_list = []
        self.URL_list = {'要闻':'https://news.qq.com/',
                         '体育': 'https://sports.qq.com/',
                         '国际': 'https://new.qq.com/ch/world/',
                         '娱乐': 'https://new.qq.com/ch/ent/',
                         '科技': 'https://new.qq.com/ch/tech/',
                         '财经': 'https://new.qq.com/ch/finance',
                         '时尚': 'https://new.qq.com/ch/fashion/',
                         '历史': 'https://new.qq.com/ch/history/',
                         '政务': 'https://new.qq.com/ch/politics/',
                         '文化': 'https://new.qq.com/ch/cul/',
                         '科学': 'https://new.qq.com/ch/kepu/',
                         }
        self.initTable()
        # self.actionOpenfile.triggered.connect(QtWidgets.QFileDialog.getOpenFileName)  # 查看当前文件夹
        # self.actionQiut.triggered.connect(self.close)  # 菜单栏退出按钮函数
        # self.actionAbout.triggered.connect(lambda: self.selectInfo("关于软件", self.aboutmsg))  # 关于软件
        # self.actionAuthor.triggered.connect(lambda: self.selectInfo("作者", self.authormsg))  # 关于作者
        self.pushButton.clicked.connect(self.startCom)  # 评论爬取开始按钮
        self.pushButton_2.clicked.connect(self.startlink)  # 新闻开始按钮
        self.pushButton_3.clicked.connect(self.export_excel)  # 新闻导出开始按钮

    def export_excel(self):

        host, user, passwd, db = '127.0.0.1', 'root', 'root', 'pynews'
        table_name = 'newsinfo'  # 要导出的表名
        self.dsrtextshow('开始导出...')
        conn = pymysql.connect(user=user, host=host, port=3306, passwd=passwd, db=db, charset='utf8')
        cur = conn.cursor()  # 建立游标
        sql = 'select * from %s;' % table_name
        cur.execute(sql)  # 执行mysql
        fileds = [filed[0] for filed in cur.description]  # 列表生成式，所有字段
        all_data = cur.fetchall()  # 所有数据
        # 写excel
        book = xlwt.Workbook()  # 先创建一个book
        sheet = book.add_sheet('sheet1')  # 创建一个sheet表
        # col = 0
        # for field in fileds: #写表头的
        #     sheet.write(0, col, field)
        #     col += 1
        # enumerate自动计算下标

        datastyle = xlwt.XFStyle()
        datastyle.num_format_str = 'yyyy-mm-dd'
        for col, field in enumerate(fileds):  # 跟上面的代码功能一样
            sheet.write(0, col, field)

        # 从第一行开始写
        row = 1  # 行数
        for data in all_data:  # 二维数据，有多少条数据，控制行数
            for col, field in enumerate(data):  # 控制列数
                if (col == 4):
                    sheet.write(row, col, field, datastyle)
                elif (col == 2):
                    sheet.write(row, col, str(field))
                else:
                    sheet.write(row, col, field)
            row += 1  # 每次写完一行，行数加1
        book.save('%s.xls' % table_name)  # 保存excel文件
        self.dsrtextshow('导出成功...')

    # 开启评论爬取线程
    def startCom(self):
        self.pushButton_2.setDisabled(True)  # 线程启动锁定按钮
        self.textEdit.setText("")  # 插入一个空白，每次启动线程都可以清屏
        # txtname = self.lineEdit_1.text()
        # product = self.changePD()
        self.comThread = comThread(self.mianTextURL_list)
        self.comThread.text_signal.connect(self.dsrtextshow)
        self.comThread.start()

    # 读取复选框内容并打开爬取新闻线程
    def startlink(self):
        print(self.comboBox.currentText())
        print(self.URL_list[str(self.comboBox.currentText())])

        self.pushButton_2.setDisabled(True)  # 线程启动锁定按钮
        self.textEdit.setText("")  # 插入一个空白，每次启动线程都可以清屏
        self.dsrthread = dsrThread()
        self.dsrthread.setMainUrl(str(self.URL_list[str(self.comboBox.currentText())]))
        self.dsrthread.result_signal.connect(self.tableFlush)
        self.dsrthread.dsrtext_signal.connect(self.dsrtextshow)
        self.dsrthread.newsList_signal.connect(self.getList)
        self.dsrthread.threadDone_signal.connect(self.newsTextThreadDone)  # 线程结束执行函数
        self.dsrthread.start()

    # 爬取结束后将评论按钮设为可用
    def newsTextThreadDone(self):
        self.pushButton_2.setDisabled(False)
        self.pushButton.setDisabled(False)

    def initTable(self):
        self.pushButton.setDisabled(True)
        self.tableView.setColumnCount(4)
        self.tableView.setHorizontalHeaderLabels(['标题', '时间', 'article_id', 'comment_id'])
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        # self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    # 重写关闭函数
    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, '关闭程序',
                                               "关闭程序可能导致正在进行的操作终止，请确认\n是否退出并关闭程序？",
                                               QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    # 消息框函数，传入2个参数，第1个是标题，第2个是显示内容
    def selectInfo(self, thetitle, megs):
        QtWidgets.QMessageBox.about(self, thetitle, megs)


    # 刷新表单槽函数
    def tableFlush(self, title, time, article_id, comment_id):
        row = self.tableView.rowCount()
        self.tableView.insertRow(row)
        print(row)
        self.tableView.setItem(row,0, QTableWidgetItem(title))
        self.tableView.setItem(row,1,QTableWidgetItem(time))
        self.tableView.setItem(row,2,QTableWidgetItem(article_id))
        self.tableView.setItem(row,3,QTableWidgetItem(comment_id))


    def getList(self, list):
        print(list)
        self.mianTextURL_list=list

    # 更新输出文本
    def dsrtextshow(self, astr):
        self.textEdit.append(astr)
        pass
# 刷新表单线程
# class dsrThread(QtCore.QThread):


# 爬取新闻正文线程
class dsrThread(QtCore.QThread):
    result_signal = QtCore.pyqtSignal(str, str, str, str)
    newsList_signal = QtCore.pyqtSignal(list)
    dsrtext_signal = QtCore.pyqtSignal(str)
    threadDone_signal = QtCore.pyqtSignal()

    mainUrl = 'https://news.qq.com/'
    pageUrlList = []

    def __init__(self, parent=None):
        super().__init__(parent)

    # 设置要爬取的站点
    def setMainUrl(self, mainUrl):
        self.mainUrl = mainUrl

    def getPage(self, url):
        return get_news_detail(url)

    def getPageUrlList(self):
        self.pageUrlList = getlist(self.mainUrl)

    def run(self):
        print('线程开始执行')
        self.dsrtext_signal.emit('爬虫线程开始执行')
        self.getPageUrlList()
        self.dsrtext_signal.emit('获取到：')
        self.dsrtext_signal.emit(str(self.pageUrlList))
        a = self.pageUrlList.__len__()
        self.dsrtext_signal.emit('共提取到 '+str(a)+'条新闻')
        i=1

        list1 = []
        for url in self.pageUrlList:
            self.dsrtext_signal.emit('当前'+str(i)+'/'+str(a)+' 条')
            i=i+1
            dict = self.getPage(url)
            self.result_signal.emit(dict['title'], dict['pubtime'], dict['article_id'], dict['comment_id'])
            temp = Detail()
            temp.comment_id = dict['comment_id']
            temp.article_id = dict['article_id']
            list1.append(list1)
        self.newsList_signal.emit(list1)#
        # self.dsrtext_signal.emit('线程测试1')
        # for i in range(0,20):
        #     self.dsrtext_signal.emit('线程测试 循环'+str(i))
        #     self.result_signal.emit(str(i)+'行', 'test1', 'test1', 'test1')
        self.threadDone_signal.emit()
        pass

class Detail:
    comment_id = ''
    article_id = ''


# 爬取评论线程
class comThread(QtCore.QThread):

    text_signal = QtCore.pyqtSignal(str)
    list = []

    def __init__(self, list, parent=None):
        super().__init__(parent)
        self.list = list

    def run(self):

        self.text_signal.emit('获取线程开始执行')
        for i in list:
            self.get_comment(i.comment_id, i.article_id)
        pass

    def get_comment(self, commentid, article_id):
        url1 = 'http://coral.qq.com/article/' + commentid + '/comment/v2?callback=_article3852524977commentv2&orinum=30&oriorder=o&pageflag=1&cursor='
        url2 = '&scorecursor=0&orirepnum=2&reporder=o&reppageflag=1&source=1&_=1555950078134'
        # 不加加头无法访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
        }

        response = getHTMLText(url1 + '0' + url2, headers)
        connection = pymysql.Connect(host=host_, port=port_, user=user_, passwd=passwd_, db=db_name_comm,
                                     charset='utf8mb4')
        print(response)
        cur = connection.cursor()
        # 创建新闻id对应的评论表
        sql = "CREATE TABLE IF NOT EXISTS pynews_comm.%s  (userid varchar(32) NOT NULL ,time datetime(0) NOT NULL,content text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,PRIMARY KEY (userid, time));" % article_id
        cur.execute(sql)
        a1 = 1
        self.text_signal.emit('开始爬取评论，每页30条评论')
        while 1:
            self.text_signal.emit('当前第 '+str(a1)+'页')
            a1 = a1 + 1
            # 截取json的正则
            g = re.search("v2\\((.+)\\)", response)
            try:
                # 装载正则
                out = json.loads(g.group(1))
            except:
                continue

            # 评论读取完成标识，while只有这一个出口
            if not out["data"]:
                print("finish！")
                break;
            if not out["data"]["last"]:
                print("finish！")
                break;

            for i in out["data"]["oriCommList"]:
                # 获取信息
                userid = i["userid"]
                # 将时间戳转化为正常时间
                time_ = str(datetime.datetime.fromtimestamp(int(i["time"])))
                content = i["content"]
                sql_(article_id, userid, time_, content)

            url = url1 + out["data"]["last"] + url2  # 得到下一个评论页面链接
            print(url)
            response = getHTMLText(url, headers)
        # 本次评论读取成功，关闭数据库连接资源
        connection.close()

    # 获取评论页面
    def getHTMLText(self, url, headers):
        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            print(r.text)
            return r.text
        except:
            return "错误 "


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myui = MainUI()
    myui.show()
    sys.exit(app.exec_())
