#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 美国股市交易时间
# 3月13日以后实行夏令时 9:30 - 16:00
# 11月6日之后实行冬令时 10:30 - 17:00


from pymongo    import MongoClient
from datetime   import datetime
import string
import re

def GetCompanyNews(company = ''):
    client      = MongoClient('localhost', 27017)
    db          = client['YahooFinanceNews']
    collection  = db['company_news']
    if company  == '':
        query   = {'corp_name': {'$ne':['']}}
    else:
        query   = {'corp_name': company}
    cursor      = collection.find(query)
    if cursor   == None:
        return None
    news_list   = list(cursor)
    client.close()
    print ('数据库中    %s  公司的新闻共  %d  条。' %(company, len(news_list)))
    return news_list


def NewsProcess(news_list):
    if news_list == None:
        return None

    Processed_News_list = []
    for news in news_list:
        if news['datetime'] == None or len(news['content']) == 0:
            continue

        # process datetime
        post_time = datetime.strptime(news['datetime'], '%Y-%m-%dT%H:%M:%S.000Z')

        # 夏令时
        if (post_time.month >3 and post_time.month < 11) or (post_time.month == 3 and post_time.day >= 13)\
            or (post_time.month == 11 and post_time.day < 6):
            # 开盘20分钟后和收盘20分钟前
            if (post_time.hour > 9 and post_time.hour < 15) or (post_time.hour == 9 and post_time.minute > 50)\
                or (post_time.hour == 15 and post_time.minute < 40):
                pass
            else:
                continue
        # 冬令时
        else:
            # 开盘20分钟后和收盘20分钟前
            if (post_time.hour > 10 and post_time.hour < 16) or (post_time.hour == 10 and post_time.minute > 50)\
                or (post_time.hour == 16 and post_time.minute < 40):
                pass
            else:
                continue            

        # process news content
        intab       = string.punctuation \
                    + '～！@＃¥％……&＊（）｛｝［］｜、；：‘’“”，。／？《》＝＋－——｀' \
                    + '！‘’“”#￥%（）*+，-。、：；《》=？@【】·~——{|} '
        outtab      = ' '*len(intab)
        transtab    = str.maketrans(intab, outtab)
        doc_lines   = []
        for line in news['content']:
            line    = line.translate(transtab).strip()         # 去除字符串中的标点符号和位于字符串左边和右边的空格
            line    = re.subn(r'[\n\r\t]+', ' ', line)[0]      # 去除字符串中间的空格
            doc_lines.append(line)
        document    = ' '.join(doc_lines)
        document    = re.subn(r' +', ' ', document)[0]

        item        = (news['corp_name'], post_time, document) 
        Processed_News_list.append(item)
    
    print ('在交易时间内发布的新闻共    %d  条。' % len(Processed_News_list))
    return Processed_News_list


if __name__ == '__main__':
    company = input('请输入公司缩写:\t')
    if company == None:
        exit(0)
    news_list = GetCompanyNews(company)
    Processed_News_list = NewsProcess(news_list)
    for i in Processed_News_list:
        print(i[0], '\t', i[1], '\t', i[2])





