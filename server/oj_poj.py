# -*- coding: utf-8 -*-
from utils import logger, updateSubmission
from exception import VSubmitFailed, VLoginFailed
from bs4 import BeautifulSoup
import html5lib
import urllib, urllib2, cookielib
import time


class POJ:
    # base information:
    URL_HOME = 'http://poj.org/'
    URL_LOGIN = URL_HOME + 'login?'
    URL_SUBMIT = URL_HOME + 'submit?'
    URL_STATUS = URL_HOME + 'status?'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/52.0.2743.116 Chrome/52.0.2743.116 Safari/537.36',
        'Origin': "http://poj.org",
        'Host': "poj.org",
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'keep-alive',
    }
    # result
    INFO = ['Run ID', 'User', 'Problem', 'Result', 'Memory', 'Time', 'Language', 'Code Length', 'Submit Time']
    # map to compatible result
    # vid v_run_id v_submit_time status time memory length language v_user
    MAP = {
        'Run ID': 'v_run_id',
        'Submit Time': 'v_submit_time',
        'Result': 'status',
        'Problem': 'vid',
        'Time': 'time',
        'Memory': 'memory',
        'Code Length': 'length',
        'Language': 'language',
        'User': 'v_user',
    }
    # language
    LANGUAGE = {
        'G++': '0',
        'GCC': '1',
        'JAVA': '2',
        'PASCAL': '3',
        'C++': '4',
        'C': '5',
        'FORTRAN': '6',
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
        try:
            data = dict(
                user_id1=self.user_id,
                password1=self.password,
                B1='login',
                url='.',
            )
            post_data = urllib.urlencode(data)
            request = urllib2.Request(POJ.URL_LOGIN, post_data, POJ.headers)

            response = self.opener.open(request, timeout=5).read()
            if response.find('loginlog') > 0:
                return True
            else:
                logger.info("login failed.")
            return False
        except Exception as e:
            logger.error(e)
            return False

    def submit(self, problem_id, language, src_code):
        try:
            self.problem_id = problem_id
            submit_data = dict(
                problem_id=problem_id,
                language=POJ.LANGUAGE[language.upper()],
                source=src_code,
                submit='Submit',
                encoded='0',
            )
            self.problem_id = problem_id
            post_data = urllib.urlencode(submit_data)
            request = urllib2.Request(POJ.URL_SUBMIT, post_data, POJ.headers)

            page = self.opener.open(request, timeout=5)
            html = page.read()
            if 'Error Occurred' in html:
                return False
            return True
        except Exception as e:
            logger.error(e)
            return False

    def result(self):
        try:
            url_data = {
                'user_id': self.user_id,
                'problem_id': self.problem_id
            }
            url = POJ.URL_STATUS + urllib.urlencode(url_data)
            page = self.opener.open(url, timeout=5)

            # sometimes you can not get the page
            if not page:
                return False, {}

            soup = BeautifulSoup(page, 'html5lib')
            table = soup.find('table', {'class': 'a'})

            if not table:
                return False, {}

            table_body = table.find('tbody')

            rows = table_body.find_all('tr')
            data = []
            for row in rows:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                data.append([ele for ele in cols])  # ! Get rid of empty values

            if len(data) <= 1:
                logger.warning('get result error!')
                return False, {}

            name = data[0]
            latest = data[1]

            if not self.run_id:
                self.run_id = latest[0]

            wait = ['Running & Judging','Compiling','Waiting']
            res = {}
            for i in range(9):
                res[POJ.MAP[name[i]]] = latest[i]

            for i in range(3):
                if res['status'] == wait[i]:
                    return False, res

            return True, res
        except Exception as e:
            logger.error(e)
            return False, {}


def poj_submit(problem_id, language_name, src_code, ip, sid, username='USTBVJ', password='USTBVJ'):
    poj = POJ(username, password)
    if poj.login():
        if poj.submit(problem_id, language_name, src_code):
            status, result = poj.result()
            while not status:
                status, result = poj.result()
                if result:
                    updateSubmission(ip, sid, result['status'])
                time.sleep(2)
            return result
        else:
            info = 'POJ [{pid},{lang},{sid}] submit error.'.format(pid=problem_id, lang=language_name, sid=sid)
            logger.exception(info)
            raise VSubmitFailed(info)
    else:
        info = 'POJ [{user},{sid}] login failed.'.format(user=username, sid=sid)
        logger.exception(info)
        raise VLoginFailed(info)

if __name__ == '__main__':
    pid = 1000
    lang = 'g++'
    src = '''
    #include<iostream>
    using namespace std;
    int main()
    {
        int a,b;
        while(cin>>a>>b)cout<<a-b<<endl;
        return 0;
    }
    '''
    poj_submit(pid, lang, src)
