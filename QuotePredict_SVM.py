#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 美国股市交易时间
# 3月13日以后实行夏令时 9:30 - 16:00
# 11月6日之后实行冬令时 10:30 - 17:00


from pymongo        import MongoClient
from collections    import defaultdict
from gensim         import corpora
from pprint         import pprint
from sklearn        import svm
from sklearn        import preprocessing
from sklearn.metrics import accuracy_score
import nltk
import string   
import re
import numpy        as np
import gensim
import time
import datetime


def GetCompanyNews(company = ''):
    client      = MongoClient('localhost', 27017)
    news_db     = client['YahooFinanceNews']
    news_collection  = news_db['company_news']
    quote_db    = client['Quote']
    quote_collection = quote_db['YahooFinanceQuote']

    if company  == '':
        query   = {'corp_name': {'$ne':['']}}
    else:
        query   = {'corp_name': company}
    cursor      = news_collection.find(query)
    if cursor   == None:
        return None

    news_list   = list(cursor) 
    print ('数据库中%s\t公司的新闻共\t%d\t条。' %(company, len(news_list)))
    if news_list == None:
        return None

    text_list = []  # text data
    quote_list  = []  # quote data

    for news in news_list:
        if news['datetime'] == None or len(news['content']) == 0:
            continue

        # process datetime
        post_time = datetime.datetime.strptime(news['datetime'], '%Y-%m-%dT%H:%M:%S.000Z')

        if post_time.year < 2016:
            continue
        if post_time.year == 2016 and post_time.month < 9:
            continue
        if post_time.year == 2016 and post_time.month == 9 and post_time.day < 20:
            continue
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

        str_year    = str(post_time.year)
        if post_time.month < 10:
            str_month   = str('0%d') % post_time.month
        else:
            str_month   = str(post_time.month)
        if post_time.day <10:
            str_day     = str('0%d') % post_time.day
        else:
            str_day     = str(post_time.day)
        d = int(str_year + str_month + str_day)
        query = {'$and':[
                        {'company'  : news['corp_name']},
                        {'date'     : d}
                        ]}
        q_cursor = quote_collection.find(query)
        if q_cursor.count() == 0:
            # print(query, 'no quote.')
            continue

        delta_6_mins = datetime.timedelta(minutes=6)
        delta_20_mins = datetime.timedelta(minutes=20)
        delta_12_hours = datetime.timedelta(hours=12)
        quote_start = 0
        quote_end   = 0

        for price in q_cursor[0]['quote']:
            q_time = datetime.datetime.fromtimestamp(price['Timestamp']) - delta_12_hours
            if post_time <= q_time and q_time <= (post_time + delta_6_mins) and quote_start == 0:
                quote_start = price['open']
                # print('post\t', post_time)
                # print('start\t', q_time)
            if (post_time + delta_20_mins) <= q_time and q_time <= (post_time + delta_20_mins + delta_6_mins) and quote_end == 0:
                quote_end   = price['open']
                # print('end\t', q_time)
                break
        if quote_start == 0 or quote_end == 0:
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
        item        = (news['corp_name'], post_time, document.lower()) 
        
        text_list.append(item)
        quote_list.append((quote_start, quote_end))

    print ('在交易时间内发布的新闻共\t%d\t条。' % len(text_list))
    client.close()

    doc_list_file = open('yahoo_finance_news.doclist', 'w')
    for i in range(len(text_list)):
        filename = "docs/yahoo_finance_news_%d" % (i)
        doc_list_file.write(filename + '\n')
        file = open(filename, 'w')
        file.write(text_list[i][2])
        file.close()
    doc_list_file.close()

    return text_list, quote_list


def GetTrainMatrix(text_list):
    texts = [nltk.word_tokenize(news[2]) for news in text_list]

    frequency = defaultdict(int)
    for text in texts:
        for token in text:
            frequency[token] += 1
    texts = [[token for token in text if frequency[token] > 1]
                for text in texts]
    
    dictionary = corpora.Dictionary(texts)
    num_of_feature = len(dictionary.keys())
    # dictionary.save('/companynews.dict')
    corpus = [dictionary.doc2bow(text) for text in texts]
    numpy_matrix = gensim.matutils.corpus2dense(corpus, num_terms=num_of_feature)
    pprint(numpy_matrix.T)
    print('shape: ', numpy_matrix.T.shape)
    return numpy_matrix.T


if __name__ == '__main__':
    company = input('请输入公司缩写:\t')
    text_list, quote_list = GetCompanyNews(company)
    X = GetTrainMatrix(text_list)
    Y = []
    for i in range(len(quote_list)):
        if quote_list[i][1] - quote_list[i][0] > 0:
            Y.append(1)
        elif quote_list[i][1] - quote_list[i][0] < 0:
            Y.append(-1)
        else:
            Y.append(0)
    t = int(len(Y) * 0.8)
    X_train = X[:t]
    X_test = X[t:]
    Y_train = Y[:t]
    Y_test = Y[t:]
    clf_lin = svm.SVC(kernel='linear', decision_function_shape='ovo')
    clf_poly = svm.SVC(kernel='poly', decision_function_shape='ovo')
    clf_rbf = svm.SVC(kernel='rbf', decision_function_shape='ovo')
    clf_lin.fit(X_train, Y_train)
    clf_poly.fit(X_train, Y_train)
    clf_rbf.fit(X_train, Y_train)
    Y_lin = clf_lin.predict(X_test)
    Y_poly = clf_poly.predict(X_test)
    Y_rbf = clf_rbf.predict(X_test)
    pprint(Y_test)
    print('Y_lin:')
    pprint(Y_lin)
    print(accuracy_score(Y_test, Y_lin))
    print('Y_poly')
    pprint(Y_poly)
    print(accuracy_score(Y_test, Y_poly))
    print('Y_rbf')
    pprint(Y_rbf)
    print(accuracy_score(Y_test, Y_rbf))



