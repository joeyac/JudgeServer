# coding=utf-8
# sudo apt-get install python-flask
# sudo apt-get install python-flask-restful
from flask import Flask, jsonify, make_response, request
from flask_restful import Api, Resource, reqparse
from werkzeug.datastructures import FileStorage
from utils import token as base_token, \
    server_info, InitIsolateEnv, logger, get_dir_hash
from flask_httpauth import HTTPTokenAuth
from language import languages
from result import RESULT, RE_RESULT
from oj_ import OJ
from config import BASE_PATH, JUDGE_DEFAULT_PATH  # '/var/local/lib/isolate/'
from compiler import Compiler
from judger import Judger
from exception import JudgeServerError, CompileError, SandboxError, \
    VSubmitFailed, VLoginFailed
from update_status import update_submission_status
from zipfile import ZipFile
from oj_poj import poj_submit
from oj_hdu import hdu_submit
from oj_cf import codeforces_submit
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
    # decorators = [auth.login_required]

    def __init__(self):
        self.flag = 'powered by crazyX for LETTers'

    def get(self):
        info = server_info()
        ip = request.remote_addr
        info['more'] = self.flag
        info['ip'] = ip
        return {'code': 0, 'data': info}


# def run(self, submission_id, language_code, code, time_limit, memory_limit, test_case_id,)
class JudgeAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()

        self.reqparse.add_argument('language_name', type=str, required=True,
                                   choices=languages.keys(),
                                   help='Only support c,c++,java,python2,python3', location='json')

        self.reqparse.add_argument('src_code', type=str, required=True, location='json')
        # ms
        self.reqparse.add_argument('time_limit', type=int, required=True, location='json')
        # kb
        self.reqparse.add_argument('memory_limit', type=int, required=True, location='json')

        self.reqparse.add_argument('test_case_id', type=str, required=True, location='json')

        self.reqparse.add_argument('submission_id', type=int, required=True, location='json')

        self.reqparse.add_argument('spj_code', type=str, location='json')

        super(JudgeAPI, self).__init__()

    @staticmethod
    def judge(args, ip):
        with InitIsolateEnv() as box_id:
            compile_config = languages[args['language_name']]['compile']
            run_config = languages[args['language_name']]['run']
            src_name = compile_config['src_name']
            time_limit = args['time_limit'] / 1000.0
            if args['language_name'] == 'java':
                memory_limit = 512 * 1024
            else:
                memory_limit = args['memory_limit']
            test_case_id = args['test_case_id']
            submission_id = args['submission_id']
	    logger.exception(test_case_id)

            path = os.path.join(JUDGE_DEFAULT_PATH, str(box_id))
            host_name = socket.gethostname()
            is_spj = True if 'spj_code' in args and args['spj_code'] else False

            # write source code into file
            try:
                src_path = os.path.join(path, 'box', src_name)
                f = open(src_path, "w")
                f.write(args['src_code'].encode("utf8"))
                f.close()
            except Exception as e:
                logger.exception(e)
                raise JudgeServerError('unable write code to file')
            # write spj code into file
            if is_spj:
                spj_src_path = os.path.join(path, 'box', 'spj.c')
                f = open(spj_src_path, "w")
                f.write(args['spj_code'].encode("utf8"))
                f.close()

            update_submission_status(ip, submission_id, 'compiling')

            # compile
            compiler = Compiler(compile_config=compile_config, box_id=box_id)
            compiler.compile()
            # compile spj code
            if is_spj:
                spj_config = languages['c++']['compile']
                spj_config['src_name'] = 'spj.c'
                spj_config['exe_name'] = 'spj'
                spj_compiler = Compiler(compile_config=spj_config, box_id=box_id)
                spj_compiler.compile()

            update_submission_status(ip, submission_id, 'running & judging')

            # run
            judger = Judger(run_config=run_config, max_cpu_time=time_limit,
                            max_memory=memory_limit, test_case_id=test_case_id,
                            box_id=box_id, server_ip=ip, submission_id=submission_id, is_spj=is_spj)
            result = judger.run()
            judge_result = {"status": RESULT["accepted"], "info": result,
                            "time": None, "memory": None, "server": host_name}
            for item in judge_result["info"]:
                if item["status"] != RESULT['accepted']:
                    judge_result["status"] = item["status"]
                    break
            else:
                st = sorted(result, key=lambda k: k['info']['time'])
                judge_result["time"] = st[-1]['info']["time"] * 1000
                # TODO 我也不知道为啥除了10之后内存和实际相符
                # 2017.04.06 update:
                # VSS - Virtual Set Size 虚拟耗用内存（包含共享库占用的内存）
                # RSS - Resident Set Size 实际使用物理内存（包含共享库占用的内存）
                # PSS - Proportional Set Size 实际使用的物理内存（比例分配共享库占用的内存）
                # USS - Unique Set Size 进程独自占用的物理内存（不包含共享库占用的内存）
                # 目前来看大概rss/10=uss
                # 经过测试 poj使用的是uss hdu使用的是rss
                judge_result["memory"] = st[-1]['info']["max-rss"]

            judge_result["status"] = RE_RESULT[judge_result["status"]]
            for item in judge_result["info"]:
                item["status"] = RE_RESULT[item["status"]]

            return judge_result

    def post(self):
        args = self.reqparse.parse_args()
        ip = request.remote_addr
        try:
            result = self.judge(args, ip)
            print result
            return {'code': 0, 'result': result}
        except CompileError as e:
            logger.exception(e)
            ret = dict()
            ret["err"] = e.__class__.__name__
            ret["data"] = e.message
            result = {"status": "compile error", "info": ret, }
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
        # TODO change the oj type to string

        self.reqparse.add_argument('problem_id', type=str, required=True, location='json')
        self.reqparse.add_argument('language_name', type=str, required=True, location='json')
        self.reqparse.add_argument('src_code', type=str, required=True, location='json')
        self.reqparse.add_argument('submission_id', type=str, required=True,
                                   help='No submission_id provided', location='json')
        self.reqparse.add_argument('username', type=str, location='json')
        self.reqparse.add_argument('password', type=str, location='json')
        super(VJudgeAPI, self).__init__()

    @staticmethod
    def virtual_judge(args):
        oj = args['oj']
        username = args['username']
        pwd = args['password']
        oj_name = OJ[oj]
        func_name = '{oj}_submit'.format(oj=oj_name)
        func = eval(func_name)
        if username:
            result = func(args['problem_id'], args['language_name'], args['src_code'],
                          args['ip'], args['submission_id'], username, pwd)
        else:
            result = func(args['problem_id'], args['language_name'], args['src_code'],
                          args['ip'], args['submission_id'],)

        return result

    def post(self):
        args = self.reqparse.parse_args()
        ip = request.remote_addr
        args['ip'] = ip
        try:
            result = self.virtual_judge(args)
            return {'code': 0, 'result': result}
        except (VLoginFailed, VSubmitFailed) as e:
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


class TestCaseHashAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('test_case_id', type=str, required=True)

    def post(self):
        args = self.reqparse.parse_args()
        test_case_id = args['test_case_id']
        path = os.path.join(BASE_PATH, 'test_case', test_case_id)
        value = get_dir_hash(path)
        return value


class SyncAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('test_case_id', type=str, required=True)
        self.reqparse.add_argument('zipfile', type=FileStorage, location='files', required=True)

    def post(self):
        args = self.reqparse.parse_args()
        test_case_id = args['test_case_id']
        s_file = args['zipfile']
        print type(test_case_id), test_case_id

        if test_case_id == 'ALL':
            aim = os.path.join(BASE_PATH, 'test_case')
        else:
            aim = os.path.join(BASE_PATH, 'test_case', str(test_case_id))
            hash_dir = os.path.join(BASE_PATH, 'test_case', 'md5', str(test_case_id))
            if os.path.exists(hash_dir):
                shutil.rmtree(hash_dir,ignore_errors=True)
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
    app.run(host='0.0.0.0')
