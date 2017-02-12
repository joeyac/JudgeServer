from utils import logger
from robobrowser import RoboBrowser
from bs4 import BeautifulSoup
from urllib2 import urlopen
import time
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
        'G++': '42',
        'C': '42',
        'G++11': '42',
        'G++14': '50',
        'GCC': '10',
        'GCC11': '1',
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
        except:
            logger.error("Open url failed.")
            return False

        enter_form['handle'] = self.user_id
        enter_form['password'] = self.password

        try:
            self.browser.submit_form(enter_form)
        except:
            logger.error("Submit login form failed.")
            return False

        try:
            checks = list(map(lambda x: x.getText()[1:].strip(),
                              self.browser.select('div.caption.titled')))
            if self.user_id not in checks:
                logger.warning("Login failed, probably incorrect password.")
                return False
        except:
            logger.error("Login status check failed.")
            return False

        return True

    def submit(self, problem_id, language, src):
        self.code_len = len(src.encode('utf-8'))
        problem_id = str(problem_id).upper()
        try:
            language = CF.LANGUAGE[str(language).upper()]
        except:
            logger.error('language unrecognizable!')
            return False

        self.browser.open(CF.URL_SUBMIT)
        submit_form = self.browser.get_form(class_='submit-form')
        submit_form['submittedProblemCode'] = problem_id
        submit_form['source'] = src
        submit_form['programTypeId'] = language

        self.browser.submit_form(submit_form)

        if self.browser.url[-6:] != 'status':
            logger.warning('Submit Failed..'
                           '(probably because you have submit the same file before.)')
            return False

        return True

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
        wait = ['Running', 'In queue']

        res = {}
        for i in range(8):
            res[CF.MAP[i]] = latest[i]
        res['length'] = '{len} B'.format(len=self.code_len)
        res['vid'] = str(res['problem']).split(' - ')[0]

        for i in range(2):
            if res['status'] == wait[i]:
                return False, res

        return True, res


def cf_submit(problem_id, language_name, src_code, username='ineedAC', password='x970307jw'):
    """
    :param problem_id: codeforces problem id, consist of contest id and problem char,like 367D
    :type problem_id: string
    :param language_name: code language name, declare in CF.LANGUAGE
    :type language_name: string
    :param src_code: source code of submission
    :type src_code: string
    :param username: submit user name, default using 'ineedAC'
    :type username: string
    :param password: submit user password, default using 'x970307jw'
    :type password: string
    :return: compatible result, if error occur, return empty dict
    :rtype: dict
    """
    logger.info('Codeforces virtual judge start.')
    cf = CF(username, password)
    if cf.login():
        logger.info('[{user}] login success.'.format(user=username))

        if cf.submit(problem_id, language_name, src_code):
            logger.info('[{pid},{lang}] submit success.'.format(pid=problem_id, lang=language_name))

            status, result = cf.result()
            while not status:
                status, result = cf.result()
                if result:
                    logger.info('status:{status}.'.format(status=result['status']))
                time.sleep(1)
            logger.info(result)
            logger.info('Codeforces virtual judge end.')
            return result
        else:
            logger.error('[{pid},{lang}] submit error.'.format(pid=problem_id, lang=language_name))
            return {}
    else:
        logger.error('[{user}] login failed.'.format(user=username))
        return {}


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
        y=m/a+(m%a==0?0:1);
        cout<<x*y<<endl;
        return 0;
        //fuck you you
    }
    '''
    cf_submit(pid, lang, src)
    # uid = 'ineedAC'
    # pwd = 'x970307jw'
    # c = CF(uid, pwd)
    # print c.result()