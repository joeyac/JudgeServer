# -*- coding: utf-8 -*-
from utils import logger
from update_status import update_submission_status
from robobrowser import RoboBrowser
from bs4 import BeautifulSoup
from urllib2 import urlopen
import time
from exception import VLoginFailed, VSubmitFailed
import html5lib


class CF:
    # base information:
    URL_HOME = 'http://codeforces.com/'
    URL_LOGIN = URL_HOME + 'enter'
    URL_SUBMIT = URL_HOME + 'problemset/submit'
    URL_STATUS = URL_HOME + 'submissions/'

    # result
    INFO = ['RunID', 'Submit Time', 'Author', 'Pro.ID', 'Language', 'Judge Status', 'Time', 'Memory']
    # map to compatible result
    # vid v_run_id v_submit_time status time memory length language v_user
    MAP = ['v_run_id', 'v_submit_time', 'v_user', 'problem', 'language', 'status', 'time', 'memory']
    # vid length

    # language
    LANGUAGE = {
        'G++': '1',
        'G++11': '42',
        'G++14': '50',
        'GCC': '10',
        'JAVA': '36',
        'PYTHON2': '7',
        'PYTHON3': '31',
    }

    def __init__(self, user_id, password):
        self.user_id = user_id
        self.password = password
        self.browser = RoboBrowser(parser='html5lib')
        self.run_id = ''
        self.pre_id = ''
        self.code_len = None

    def login(self):
        try:
            self.browser.open(CF.URL_LOGIN)
            enter_form = self.browser.get_form('enterForm')
        except Exception as e:
            logger.exception(e)
            logger.error("Open url failed.")
            return False

        enter_form['handle'] = self.user_id
        enter_form['password'] = self.password

        try:
            self.browser.submit_form(enter_form)
        except Exception as e:
            logger.exception(e)
            logger.error("Submit login form failed.")
            return False

        try:
            checks = list(map(lambda x: x.getText()[1:].strip(),
                              self.browser.select('div.caption.titled')))
            if self.user_id not in checks:
                logger.warning("Login failed, probably incorrect password.")
                return False
        except Exception as e:
            logger.exception(e)
            logger.error("Login status check failed.")
            return False

        return True

    def submit(self, problem_id, language, src_code):
        self.code_len = len(src_code.encode('utf-8'))
        problem_id = str(problem_id).upper()
        try:
            language = CF.LANGUAGE[str(language).upper()]
        except Exception as e:
            logger.exception(e)
            logger.error('language unrecognizable!')
            return False

        self.browser.open(CF.URL_SUBMIT)
        submit_form = self.browser.get_form(class_='submit-form')
        submit_form['submittedProblemCode'] = problem_id
        submit_form['source'] = src_code
        submit_form['programTypeId'] = language

        self.browser.submit_form(submit_form)

        if self.browser.url[-6:] != 'status':
            logger.warning('Submit Failed..'
                           '(probably because you have submit the same file before.)')
            return False

        return True

    @staticmethod
    def str2int(string):
        if not string:
            return 0
        string = str(string)[:-2]
        return int(string)

    def result(self):
        url = CF.URL_STATUS + str(self.user_id)
        page = urlopen(url, timeout=5)
        soup = BeautifulSoup(page, 'html5lib')

        table = soup.find('table', {'class': 'status-frame-datatable'})
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
        data = []
        for row in rows:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            data.append([ele.replace(u'\xa0', u' ') for ele in cols if ele])  # No need:Get rid of empty values

        latest = data[1]
        wait = ['running', 'in queue']

        res = {}
        for i in range(8):
            res[CF.MAP[i]] = str(latest[i]).lower()
        res['length'] = '{len} B'.format(len=self.code_len)
        res['vid'] = str(res['problem']).split(' - ')[0]

        res['time'] = self.str2int(res['time'])
        res['memory'] = self.str2int(res['memory'])

        for i in range(2):
            if wait[i] in res['status']:
                return False, res

        return True, res


def codeforces_submit(problem_id, language_name, src_code, ip=None, sid=None, username='ineedAC', password='USTBVJ'):
    cf = CF(username, password)
    if cf.login():

        if cf.submit(problem_id, language_name, src_code):
            status, result = cf.result()
            while not status:
                status, result = cf.result()
                if result and ip:
                    update_submission_status(ip, sid, result['status'])
                time.sleep(2)
            return result
        else:
            info = 'Codeforces [{pid},{lang},{sid}] submit error.'.format(pid=problem_id, lang=language_name, sid=sid)
            logger.exception(info)
            raise VSubmitFailed(info)
    else:
        info = 'Codeforces [{user},{sid}] login failed.'.format(user=username, sid=sid)
        logger.exception(info)
        raise VLoginFailed(info)


if __name__ == '__main__':
    pid = '1A'
    lang = 'g++'
    src = '''
    #include <iostream>
    using namespace std;
    int n,m,a;
    long long x,y;
    int main() {
        cin>>n>>m>>a;
        x=n/a+(n%a==0?0:1);
        y=m/a+(m%a==0?0:1);//sadjiowdqwdw
        cout<<x*y<<endl;
        return 0;
        //fuck you you
    }
    '''
    print codeforces_submit(pid, lang, src)
