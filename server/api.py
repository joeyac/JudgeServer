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
from utils import token as base_token, server_info, InitIsolateEnv, logger
from flask_httpauth import HTTPTokenAuth
from language import languages
from result import RESULT
from config import JUDGE_DEFAULT_PATH  # '/var/local/lib/isolate/'
from compiler import Compiler
from judger import Judger
from exception import JudgeServerError, CompileError, SandboxError
import socket
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


# def run(self,submission_id, language_code, code, time_limit, memory_limit, test_case_id,)
class JudgeAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()

        self.reqparse.add_argument('language_code', type=int, required=True,
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

        self.reqparse.add_argument('submission_id', type=str, location='json')
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
            # write source code into file
            try:
                src_path = os.path.join(path, 'box', src_name)
                f = open(src_path, "w")
                f.write(args['code'].encode("utf8"))
                f.close()
            except Exception as e:
                raise JudgeServerError('unable write code to file')

            # compile
            compiler = Compiler(compile_config=compile_config, box_id=box_id)
            exe_name = compiler.compile()

            # run
            judger = Judger(run_config=run_config,max_cpu_time=time_limit, max_memory=memory_limit,
                            test_case_id=test_case_id, box_id=box_id)
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

            return result
        except (JudgeServerError, CompileError, SandboxError) as e:
            logger.exception(e)
            ret = dict()
            ret["err"] = e.__class__.__name__
            ret["data"] = e.message
            return ret
        except Exception as e:
            logger.exception(e)
            ret = dict()
            ret["err"] = "JudgeClientError"
            ret["data"] = e.__class__.__name__ + ":" + e.message
            return ret


api.add_resource(PingAPI, '/ping/', endpoint='ping')
api.add_resource(JudgeAPI, '/judge/', endpoint='judge')

if __name__ == '__main__':
    app.run(debug=True)