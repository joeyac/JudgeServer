from utils import logger
from robobrowser import RoboBrowser
from bs4 import BeautifulSoup
from urllib2 import urlopen


class CF:
    # base information:
    URL_HOME = 'http://codeforces.com/'
    URL_LOGIN = URL_HOME + 'enter'
    URL_SUBMIT = URL_HOME + 'problemset/submit'
    URL_STATUS = URL_HOME + 'submissions/'

    # result
    INFO = ['RunID', 'Submit Time', 'Author', 'Pro.ID', 'Language', 'Judge Status', 'Time', 'Memory']

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
        self.browser = RoboBrowser()
        self.run_id = ''
        self.pre_id = ''

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

        logger.info('Login Successful!')
        return True

    def submit(self, problem_id, language, src):
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

        logger.info('Submit Successful')
        return True

    def init_id(self):
        if self.pre_id != '':
            return True
        url = CF.URL_STATUS + str(self.user_id)
        page = urlopen(url, timeout=5)
        soup = BeautifulSoup(page, 'html5lib')
        tables = soup.find('table', {'class': 'status-frame-datatable'})
        tmp = []
        for row in tables.findAll('tr'):
            cols = row.findAll('td')
            cols = [ele.text.strip() for ele in cols]
            tmp = [ele.replace(u'\xa0', u' ') for ele in cols if ele]
            if len(tmp) == 8:
                break
        self.pre_id = tmp[0]
        return True

    def result(self):
        url = CF.URL_STATUS + str(self.user_id)
        page = urlopen(url, timeout=5)
        soup = BeautifulSoup(page, 'html5lib')

        tables = soup.find('table', {'class': 'status-frame-datatable'})
        tmp = []
        find = False
        for row in tables.findAll('tr'):
            cols = row.findAll('td')
            cols = [ele.text.strip() for ele in cols]
            tmp = [ele.replace(u'\xa0', u' ') for ele in cols if ele]
            if len(tmp) == 8:
                if tmp[0] == self.pre_id:
                    break
                if not find:
                    if self.run_id == '' or self.run_id == tmp[0]:
                        find = True
                        self.run_id = tmp[0]
            if find:
                break
        if not find:
            logger.info("Can not find submissions!")
            return True