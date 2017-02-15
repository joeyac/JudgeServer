# -*- coding: utf-8 -*-
from utils import logger, updateSubmission
from exception import VLoginFailed, VSubmitFailed
from bs4 import BeautifulSoup
import html5lib
import urllib, urllib2, cookielib
import time


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
    INFO = ['Run ID', 'Submit Time', 'Judge Status', 'Pro.ID', 'Exe.Time', 'Exe.Memory', 'Code Len.', 'Language',
            'Author']
    # map to compatible result
    # vid v_run_id v_submit_time status time memory length language v_user
    MAP = {
        'Run ID': 'v_run_id',
        'Submit Time': 'v_submit_time',
        'Judge Status': 'status',
        'Pro.ID': 'vid',
        'Exe.Time': 'time',
        'Exe.Memory': 'memory',
        'Code Len.': 'length',
        'Language': 'language',
        'Author': 'v_user',
    }
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
                return True
            else:
                logger.warning("Login failed.")
                return False
        except:
            logger.error("Login method error.")
            return False

    def submit(self, problem_id, language, src_code):
        submit_data = dict(
            problemid=problem_id,
            language=HDU.LANGUAGE[language.upper()],
            usercode=src_code,
            check='0',
        )
        self.problem_id = problem_id
        post_data = urllib.urlencode(submit_data)
        try:
            request = urllib2.Request(HDU.URL_SUBMIT, post_data, HDU.headers)
            self.opener.open(request)
            return True
        except:
            logger.info('Submit method error.')
            return False

    def result(self):
        data = {
                'first': '',
                'pid': '',
                'user': self.user_id,
                }
        if self.run_id:
            data['first'] = self.run_id
        if self.problem_id:
            data['pid'] = self.problem_id

        url = HDU.URL_STATUS + urllib.urlencode(data)

        try:
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
                data.append([ele for ele in cols])  # No need:Get rid of empty values

            if len(data) <= 1:
                logger.warning('get result error!')
                return False, {}

            name = data[0]
            latest = data[1]

            if not self.run_id:
                self.run_id = latest[0]

            wait = ['Queuing', 'Compiling', 'Running']

            res = {}
            for i in range(9):
                res[HDU.MAP[name[i]]] = latest[i]

            for i in range(3):
                if res['status'] == wait[i]:
                    return False, res

            return True, res

        except Exception as e:
            logger.error(e)
            return False, {}


def hdu_submit(problem_id, language_name, src_code, ip, sid, username='USTBVJ', password='USTBVJ'):
    hdu = HDU(username, password)
    if hdu.login():
        if hdu.submit(problem_id, language_name, src_code):
            status, result = hdu.result()
            while not status:
                status, result = hdu.result()
                if result:
                    updateSubmission(ip, sid, result['status'])
                time.sleep(2)
            return result
        else:
            info = 'HDU [{pid},{lang},{sid}] submit error.'.format(pid=problem_id, lang=language_name, sid=sid)
            logger.exception(info)
            raise VSubmitFailed(info)
    else:
        info = 'HDU [{user},{sid}] login failed.'.format(user=username, sid=sid)
        logger.exception(info)
        raise VLoginFailed(info)


if __name__ == '__main__':
    pid = 1000
    lang = 'g++'
    src = '''
    #include<bits/stdc++.h>
    using namespace std;
    int main()
    {
        int a,b;
        while(cin>>a>>b)cout<<a-b<<endl;
        return 0;
    }
    '''
    hdu_submit(pid,lang,src)
