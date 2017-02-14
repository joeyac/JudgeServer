# coding=utf-8
# sudo apt-get install python-flask
# sudo apt-get install python-flask-restful
# ===========   ===================================================             ==============
# HTTP method   URL                                                             action
# ===========   ===================================================             ==============
# POST          http://[hostname]/api/                                          new judge_task
# GET           http://[hostname]/api/                                          get server_status

# GET           http://[hostname]/api/[submission_id]                           get judge_status
# POST          http://[hostname]/api/[submission_id]                           update judge_task
from flask import Flask, jsonify, make_response
from flask_restful import Api, Resource, reqparse
from werkzeug.datastructures import FileStorage
from utils import token as base_token, \
    server_info, InitIsolateEnv, logger, getHashOfDir
from flask_httpauth import HTTPTokenAuth
from language import languages
from result import RESULT
from oj_ import OJ
from config import BASE_PATH, JUDGE_DEFAULT_PATH  # '/var/local/lib/isolate/'
from compiler import Compiler
from judger import Judger
from exception import JudgeServerError, CompileError, SandboxError
from zipfile import ZipFile
from oj_poj import poj_submit
from oj_hdu import hdu_submit
from oj_cf import cf_submit
import socket
import shutil
import os


app = Flask(__name__)
api = Api(app)
auth = HTTPTokenAuth(scheme='Token')


@auth.verify_token
def verify_token(token):
    # 3c469e9d6c5875d37a43f353d4f88e61fcf812c66eee3457465a40b0da4153e0
    # print token
    # print TOKEN
    return token == base_token


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)


class PingAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()

        self.reqparse.add_argument('language_code', type=int, required=True,
                                   help='No language_code provided', location='json')
        self.reqparse.add_argument('data', type=dict, location='json')

    def get(self):
        info = server_info()
        return {'info': info}

    def post(self):
        args = self.reqparse.parse_args()
        print args['language_code']
        return {'info': languages[args['language_code']]}


# def run(self, submission_id, language_code, code, time_limit, memory_limit, test_case_id,)
class JudgeAPI(Resource):
    decorators = [auth.login_required]
    """
    :param submission_id: for async update judge status
    :type submission_id: string
    :param language_code: language code, declare in language.py, range[1,5]
    :type language_code: int
    :param code: source code of submission
    :type code: string
    :param time_limit: time limit of the problem
    :type time_limit: int
    :param memory_limit: memory limit of the problem
    :type memory_limit: int
    :param test_case_id: test_case_id
    :type test_case_id: string
    :return: {'code':code, 'result':result}
                code = 0 success
                code = 1 catch error
                code = 2 unknown error
    :rtype: dict
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()

        self.reqparse.add_argument('language_code', type=int, required=True,
                                   choices=languages.keys(),
                                   help='No language_code provided', location='json')
        self.reqparse.add_argument('code', type=str, required=True,
                                   help='No user code provided', location='json')

        #  ms
        self.reqparse.add_argument('time_limit', type=int, required=True,
                                   help='No time_limit provided', location='json')

        # kb
        self.reqparse.add_argument('memory_limit', type=int, required=True,
                                   help='No memory_limit provided', location='json')

        self.reqparse.add_argument('test_case_id', type=str, required=True,
                                   help='No test_case_id provided', location='json')

        self.reqparse.add_argument('spj_code', type=str, location='json')

        self.reqparse.add_argument('submission_id', type=str, required=True,
                                   help='No submission_id provided', location='json')
        super(JudgeAPI, self).__init__()

    def judge(self, args):
        with InitIsolateEnv() as box_id:
            compile_config = languages[args['language_code']]['compile']
            run_config = languages[args['language_code']]['run']
            src_name = compile_config['src_name']
            time_limit = args['time_limit'] / 1000.0
            memory_limit = args['memory_limit']
            test_case_id = args['test_case_id']
            path = os.path.join(JUDGE_DEFAULT_PATH, str(box_id))
            host_name = socket.gethostname()
            is_spj = True if 'spj_code' in args else False

            # write source code into file
            try:
                src_path = os.path.join(path, 'box', src_name)
                f = open(src_path, "w")
                f.write(args['code'].encode("utf8"))
                f.close()
            except Exception as e:
                raise JudgeServerError('unable write code to file')
            # write spj code into file
            if is_spj:
                spj_src_path = os.path.join(path, 'box', 'spj.c')
                f = open(spj_src_path, "w")
                f.write(args['spj_code'].encode("utf8"))
                f.close()

            # compile
            compiler = Compiler(compile_config=compile_config, box_id=box_id)
            exe_name = compiler.compile()
            # compile spj code
            if is_spj:
                spj_config = languages[1]['compile']
                spj_config['src_name'] = 'spj.c'
                spj_config['exe_name'] = 'spj'
                spj_compiler = Compiler(compile_config=spj_config, box_id=box_id)
                spj_name = spj_compiler.compile()

            # run
            judger = Judger(run_config=run_config,max_cpu_time=time_limit, max_memory=memory_limit,
                            test_case_id=test_case_id, box_id=box_id, is_spj=is_spj)
            result = judger.run()
            judge_result = {"status": RESULT["accepted"], "info": result,
                            "accepted_answer_time": None, "server": host_name}
            for item in judge_result["info"]:
                if item["status"] != RESULT['accepted']:
                    judge_result["status"] = item["status"]
                    break
            else:
                st = sorted(result, key=lambda k: k['meta']['time'])
                judge_result["accepted_answer_time"] = st[-1]['meta']["time"]
            return judge_result

    def post(self):
        args = self.reqparse.parse_args()
        try:
            result = self.judge(args)
            return {'code': 0, 'result': result}
        except CompileError as e:
            logger.exception(e)
            ret = dict()
            ret["err"] = e.__class__.__name__
            ret["data"] = e.message
            result = {"status": RESULT["compile_error"], "info": ret, }
            return {'code': 0, 'result': result}
        except (JudgeServerError, SandboxError) as e:
            logger.exception(e)
            ret = dict()
            ret["err"] = e.__class__.__name__
            ret["data"] = e.message
            return {'code': 1, 'result': ret}
        except Exception as e:
            logger.exception(e)
            ret = dict()
            ret["err"] = "JudgeClientError"
            ret["data"] = e.__class__.__name__ + ":" + e.message
            return {'code': 2, 'result': ret}


class VJudgeAPI(Resource):
    decorators = [auth.login_required]
    # problem_id, language_name, src_code

    def __init__(self):
        self.reqparse = reqparse.RequestParser()

        self.reqparse.add_argument('oj', type=int, choices=OJ.keys(), required=True, location='json')
        self.reqparse.add_argument('problem_id', type=str, required=True, location='json')
        self.reqparse.add_argument('language_name', type=str, required=True, location='json')
        self.reqparse.add_argument('src_code', type=str, required=True, location='json')
        self.reqparse.add_argument('submission_id', type=str, required=True,
                                   help='No submission_id provided', location='json')
        self.reqparse.add_argument('username', type=str, location='json')
        self.reqparse.add_argument('password', type=str, location='json')
        super(VJudgeAPI, self).__init__()

    def vjudge(self, args):
        oj = args['oj']
        username = args['username']
        pwd = args['password']
        result = {}
        if oj == 1: # poj
            if username:
                result = poj_submit(args['problem_id'], args['language_name'], args['src_code'],
                                    username, pwd)
            else:
                result = poj_submit(args['problem_id'], args['language_name'], args['src_code'])
        elif oj == 2: # hdu
            if username:
                result = hdu_submit(args['problem_id'], args['language_name'], args['src_code'],
                                    username, pwd)
            else:
                result = hdu_submit(args['problem_id'], args['language_name'], args['src_code'])
        elif oj == 3: # codeforces
            if username:
                result = cf_submit(args['problem_id'], args['language_name'], args['src_code'],
                                   username, pwd)
            else:
                result = cf_submit(args['problem_id'], args['language_name'], args['src_code'])
        return result

    def post(self):
        args = self.reqparse.parse_args()
        print args
        try:
            result = self.vjudge(args)
            return {'code': 0, 'result': result}
        except Exception as e:
            logger.exception(e)
            ret = dict()
            ret["err"] = "JudgeClientError"
            ret["data"] = e.__class__.__name__ + ":" + e.message
            return {'code': 2, 'result': ret}


class TestCaseHashAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('test_case_id', type=str, required=True)

    def post(self):
        args = self.reqparse.parse_args()
        test_case_id = args['test_case_id']
        path = os.path.join(BASE_PATH, 'test_case', test_case_id)
        value = getHashOfDir(path)
        return value


class SyncAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('test_case_id', type=str, required=True)
        self.reqparse.add_argument('file', type=FileStorage, location='files', required=True)

    def post(self):
        args = self.reqparse.parse_args()
        test_case_id = args['test_case_id']
        s_file = args['file']

        if test_case_id == 'ALL':
            aim = os.path.join(BASE_PATH, 'test_case')
        else:
            aim = os.path.join(BASE_PATH, 'test_case', str(test_case_id))
        if os.path.exists(aim):
            shutil.rmtree(aim, ignore_errors=True)

        os.mkdir(aim)
        os.chmod(aim, 0777)

        path = os.path.join('/tmp', s_file.filename)
        s_file.save(path)

        zipfile = ZipFile(path)
        for sub_file in zipfile.namelist():
            zipfile.extract(sub_file, aim)
            os.chmod(os.path.join(aim, sub_file), 0777)
        zipfile.close()

        os.remove(path)
        return "Done!"

api.add_resource(PingAPI, '/ping/', endpoint='ping')
api.add_resource(JudgeAPI, '/judge/', endpoint='judge')
api.add_resource(VJudgeAPI, '/vjudge/', endpoint='vjudge')
api.add_resource(TestCaseHashAPI, '/hash/', endpoint='hash')
api.add_resource(SyncAPI, '/sync/', endpoint='sync')

if __name__ == '__main__':
    app.run(debug=True)

