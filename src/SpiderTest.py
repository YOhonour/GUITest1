from bs4 import BeautifulSoup
from selenium import webdriver
import requests
import re
import json
# import MySQLdb
import datetime
import pymysql

user_ = 'root'
passwd_ = 'root'
db_name_comm = 'pynews_comm'
db_name_pynews = 'pynews'
host_ = '127.0.0.1'
port_ = 3306


def getlist(mianurl):
    driver = webdriver.PhantomJS()
    driver.get(mianurl)
    print(driver.title)

    pagesource = driver.page_source
    # print(pageSource)
    bsObj = BeautifulSoup(pagesource, "html.parser")
    # t1 = bsObj.find_all(class_='item cf')
    t1 = bsObj.find_all("a")
    # 目标正则匹配
    regex = 'https?.*/20\d{6}.*html?'
    # regex = 'https?.*/20\d{6}.*NEW2019\d{12}'
    urllist = []

    # 遍历a标签内href，对比是否为新闻标签,匹配成功加入列表中
    for t2 in t1:
        t3 = str(t2.get('href'))
        if re.match(regex, t3) is not None:
            urllist.append(t3)
            # print(t3)
    connection = pymysql.connect(host=host_, port=port_, user=user_, passwd=passwd_, db=db_name_pynews, charset='utf8mb4')
    cur = connection.cursor()
    # sql1 = 'CREATE TABLE IF NOT EXISTS pynews.newsinfo ( article_id varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL, url varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, comment_id int(11) NULL DEFAULT NULL, title varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL, pubtime datetime(0) NULL DEFAULT NULL, text text CHARACTER SET utf8 COLLATE utf8_general_ci NULL, PRIMARY KEY (article_id) );'
    # 这里修改了下，comment_id之前使用的int表示，数据范围可能不够，我这里改为使用varchar表示
    sql1 = 'CREATE TABLE IF NOT EXISTS pynews.newsinfo ( article_id varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL, url varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL, comment_id varchar(128) NULL DEFAULT NULL, title varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL, pubtime datetime(0) NULL DEFAULT NULL, text text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL, PRIMARY KEY (article_id) );'

    cur.execute(sql1)
    urllist = list(set(urllist))
    return urllist


def get_news_detail(url):
    driver = webdriver.PhantomJS()
    driver.get(url)
    page_source = driver.page_source
    # print(page_source)
    bsObj = BeautifulSoup(page_source, "html.parser")
    # t1 = bsObj.find_all(class_='item cf')
    t1 = bsObj.find_all("p", class_='one-p')
    # print("提取到：=======================")
    # print(t1)
    str_text = str(t1)
    # 将段落分隔改为换行符
    str_text1 = str_text.replace('</p>, <p class="one-p">', '\n')
    # 去除包含的图片标签
    str_text5 = re.sub('\n?<.+/i?p?>\n?', '', str_text1)
    # str_text5 = re.sub('<.+"/>', '\n', str_text5)
    str_text5 = str_text5.replace('[<p class="one-p">', '')
    str_text5 = str_text5.replace('</p>]', '')
    # 非贪婪匹配 将多余的<strong>标签去除
    str_text6 = re.sub('<.+?>', '', str_text5)
    # 检索所有script标签
    str6 = bsObj.findAll('script')
    result_text = str(str6);
    # 为取出script中对应的值，对应的正则
    pattern = re.compile(r"\"title\": \"(.*?)\"")
    pattern1 = re.compile(r"\"comment_id\": \"(.*?)\"")
    pattern2 = re.compile(r"\"article_id\": \"(.*?)\"")
    pattern2_1 = re.compile(r"\"cms_id\": \"(.*?)\"")

    pattern3 = re.compile(r"\"pubtime\": \"(.*?)\"")

    # 如果没有新闻信息直接结束本次爬取
    try:
        comment_id = pattern1.search(result_text).group(1)
    except:
        return 0
    # 获取值
    article_id = ''
    try:
        article_id = pattern2.search(result_text).group(1)
    except:
        print("article_id 不存在")
        try:
            article_id = pattern2_1.search(result_text).group(1)
        except:
            print("cms_ID 不存在")


    title = pattern.search(result_text).group(1)
    pubtime = pattern3.search(result_text).group(1)

    # 将值存入字典
    dict_ = {"article_id": str(article_id), "url": url, "title": str(title), "pubtime": str(pubtime),
             "comment_id": str(comment_id), "text": str_text6}
    print(dict_)
    connection = pymysql.connect(host=host_, port=port_, user=user_, passwd=passwd_, db=db_name_pynews, charset='utf8mb4')

    try:
        cur = connection.cursor()

        # 这里主要MYSQl语句内的VALUES(xxx)中的问题，对于varchar类型的数据，要使用''括起来
        sql = "INSERT INTO pynews.newsinfo( article_id, comment_id, title, pubtime, url, text) VALUES ('{}', '{}', '{}', '{}', '{}', '{}')".format(
            dict_['article_id'], dict_['comment_id'], dict_['title'], dict_['pubtime'], dict_['url'],
            dict_['text'])

        cur.execute(sql)
        connection.commit()
        print("插入新闻数据成功")
    except:
        connection.rollback()
        print("插入新闻数据失败")

    connection.close()
    # 将新闻信息返回，用以爬取评论

    return dict_


# 对评论进行储存
def sql_(article_id, userid, time_, content):
    connection = pymysql.connect(host=host_, port=port_, user=user_, passwd=passwd_, db=db_name_comm,
                                 charset='utf8mb4')
    sql_ = "INSERT INTO pynews_comm.%s(userid, time, content) VALUES ('%s','%s','%s')" % (
        str(article_id), str(userid), time_, content)

    print(sql_)
    try:
        cur = connection.cursor()
        cur.execute(sql_)
        connection.commit()
        print("插入评论数据成功")
    except pymysql.err.InternalError:
        # 这里MySQl插入EMOJI有问题，会直接报错
        print("插入评论数据失败，评论中含有Emoji")
        connection.rollback()

    #     如果数据库中已经存在这一条评论则一定会插入失败，因为主键重复
    except:
        print("插入评论数据失败")


# 获取新闻评论id为commentid，新闻id为article_id的所有评论
def get_comment(commentid, article_id):
    url1 = 'http://coral.qq.com/article/' + commentid + '/comment/v2?callback=_article3852524977commentv2&orinum=30&oriorder=o&pageflag=1&cursor='
    url2 = '&scorecursor=0&orirepnum=2&reporder=o&reppageflag=1&source=1&_=1555950078134'
    # 不加加头无法访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
    }

    response = getHTMLText(url1 + '0' + url2, headers)
    connection = pymysql.Connect(host=host_, port=port_, user=user_, passwd=passwd_, db=db_name_comm, charset='utf8mb4')
    print(response)
    cur = connection.cursor()
    # 创建新闻id对应的评论表
    sql = "CREATE TABLE IF NOT EXISTS pynews_comm.%s  (userid varchar(32) NOT NULL ,time datetime(0) NOT NULL,content text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,PRIMARY KEY (userid, time));" % article_id
    cur.execute(sql)

    while 1:
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
def getHTMLText(url, headers):
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        print(r.text)
        return r.text
    except:
        return "错误 "


# 创建数据库（如果已经存在就不创建）
def create_databases():
    connection = pymysql.connect(host=host_, port=port_, user=user_, password=passwd_, charset='utf8mb4')
    cur = connection.cursor()
    sql1 = 'CREATE DATABASE IF NOT EXISTS {};'.format(db_name_pynews)
    sql2 = 'CREATE DATABASE IF NOT EXISTS {};'.format(db_name_comm)
    try:
        cur.execute(sql1)
        cur.execute(sql2)
    except:
        print("数据库创建失败\n")


def main():
    # news_url_list_ = getlist('https://news.qq.com/')
    # https://new.qq.com/ch/world/
    create_databases()
    news_url_list_ = getlist('https://news.qq.com')
    news_url_list_ = list(set(news_url_list_))
    print(news_url_list_)
    print("新闻条数：" + str(len(news_url_list_)))

    for url in news_url_list_:
        taill = get_news_detail(url)
        if taill == 0:
            continue
        get_comment(taill['comment_id'], taill['article_id'])

    print("---------------所有新闻评论拉取完毕！---------------")

if __name__ == '__main__':
    main()

# sql_('20190422a0ldyk', '875683846','2019-04-23 15:05:42','外形好科幻，中国一级棒厉害啊！我的祖国。')
# print(getlist('https://news.qq.com/'))
# taill = get_news_detail('https://new.qq.com/omn/20190423/20190423A04HBK.html')
# # print(taill)
#
# get_comment(taill['comment_id'],taill['article_id'])
# crawlcomment('3853011110','1')
