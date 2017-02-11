# -*- coding: utf-8 -*-
from utils import logger
from bs4 import BeautifulSoup
import re
import html5lib
import urllib, urllib2, cookielib


class HDU:
    # base information:
    URL_HOME = 'http://acm.hdu.edu.cn/'
    URL_LOGIN = URL_HOME + 'userloginex.php?action=login'
    URL_SUBMIT = URL_HOME + 'submit.php?action=submit'
    URL_STATUS = URL_HOME + 'status.php?'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Ubuntu Chromium/52.0.2743.116 Chrome/52.0.2743.116 Safari/537.36',
        'Origin': "http://acm.hdu.edu.cn",
        'Host': "acm.hdu.edu.cn",
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'keep-alive',
    }

    # result
    INFO = ['RunID', 'Submit Time', 'Judge Status', 'Pro.ID', 'Exe.Time', 'Exe.Memory', 'Code Len', 'Language',
            'Author']
    # language
    LANGUAGE = {
        'G++': '0',
        'GCC': '1',
        'C++': '2',
        'C': '3',
        'PASCAL': '4',
        'JAVA': '5',
        'C#': '6',
    }

    def __init__(self, user_id, password):
        self.user_id = user_id
        self.password = password
        self.problem_id = ''
        self.run_id = ''

        # 声明一个CookieJar对象实例来保存cookie
        cookie = cookielib.CookieJar()
        # 利用urllib2库的HTTPCookieProcessor对象来创建cookie处理器
        handler = urllib2.HTTPCookieProcessor(cookie)
        # 通过handler来构建opener
        self.opener = urllib2.build_opener(handler)
        # 此处的open方法同urllib2的urlopen方法，也可以传入request

    def login(self):
        data = dict(
            username=self.user_id,
            userpass=self.password,
            login='Sign In'
        )
        try:
            post_data = urllib.urlencode(data)
            request = urllib2.Request(HDU.URL_LOGIN, post_data, HDU.headers)
            response = self.opener.open(request).read()
            if response.find('signout') > 0:
                logger.info("Login successful!")
                return True
            else:
                logger.warning("Login failed.")
                return False
        except:
            logger.error("Login method error.")
            return False

    def submit(self, problem_id, language, src):
        submit_data = dict(
            problemid=problem_id,
            language=HDU.LANGUAGE[language.upper()],
            usercode=src,
            check='0',
        )
        self.problem_id = problem_id
        post_data = urllib.urlencode(submit_data)
        try:
            request = urllib2.Request(HDU.URL_SUBMIT, post_data, HDU.headers)
            self.opener.open(request)
            logger.info('Submit successful!')
            return True
        except:
            logger.info('Submit method error.')
            return False

    def result(self):
        data = {
                'first':'',
                'pid':'',
                'user':self.user_id,
                }
        if self.run_id:
            data['first'] = self.run_id
        if self.problem_id:
            data['pid'] = self.problem_id

        url = HDU.URL_STATUS + urllib.urlencode(data)
        print url
        request = urllib2.Request(url, '', HDU.headers)
        page = self.opener.open(request, timeout=5)

        soup = BeautifulSoup(page, 'html5lib')
        table = soup.find('table', {'class': 'table_text'})
        table_body = table.find('tbody')

        rows = table_body.find_all('tr')

        data = []
        for row in rows:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            data.append([ele for ele in cols if ele])  # Get rid of empty values

        if len(data) <= 1:
            logger.warning('get result error!')
            return False, {}

        name = data[0]
        latest = data[1]

        if not self.run_id:
            self.run_id = latest[0]

        wait = ['Queuing', 'Compiling', 'Running']
        for i in range(3):
            if latest[2] == wait[i]:
                return False, latest

        res = {}
        for i in range(9):
            res[name[i]]=latest[i]
        return True, res




if __name__ == '__main__':
    user_id = 'USTBVJ'
    pwd = 'USTBVJ'
    pid = 1000
    lang = 'g++'
    src = '''
    #include<stdio.h>
    int main()
    {
        int a,b;
        while(cin>>a>>b)cout<<a+b<<endl;
        return 0;
    }

    '''
    HDU = HDU(user_id, pwd)
    HDU.login()
    if HDU.submit(pid, lang, src):
        status, result = HDU.result()
        import time
        result = {}
        while not status:  # 每隔1s检测一次结果
            status, result = HDU.result()
            time.sleep(1)
        print result
        print 'done!'
