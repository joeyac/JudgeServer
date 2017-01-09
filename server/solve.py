import os
import socket
import shutil

from utils import logger, server_info
from compiler import Compiler
from judger import Judger
from language import languages
from result import RESULT
from config import JUDGE_DEFAULT_PATH  # '/var/local/lib/isolate/'
from config import DEBUG
from exception import JudgeServerError
import commands


class JudgeServer(object):
    def ping(self):
        data = server_info()
        data['action'] = 'ping'
        return data

    # 0 C 1 C++ 2 JAVA 3 PYTHON2
    def run(self, token, submission_id, language_code, code, time_limit, memory_limit, test_case_id,):
        print token
        host_name = socket.gethostname()
        language = languages[language_code]
        if not token or token != 'crazyX':
            if token:
                logger.info("Invalid token: " + token)
            return {"code": 2, "data": {"error": "Invalid token", "server": host_name}}
        box_id = choose_box_id()
        if not box_id:
            return {"code": 3, "data": {"error": "sandbox id not enough", "server": host_name}}
        status = init_env(box_id)
        path = os.path.join(JUDGE_DEFAULT_PATH, str(box_id))
        box_path = os.path.join(path, 'box')
        if status != 0:
            remove_env(box_id)
            return {"code": 2, "data": {"error": "init env failed", "server": host_name}}

        # write code
        try:
            src_path = os.path.join(box_path, language['compile']['src_name'])
            f = open(src_path, "w")
            f.write(code.encode("utf8"))
            f.close()
        except Exception as e:
            remove_env(box_id)
            return {"code": 2, "data": {"error": str(e), "server": host_name}}

        # compile
        try:
            compiler = Compiler(compile_config=language['compile'],box_id=box_id)
            exe_name = compiler.compile()
        except Exception as e:
            remove_env(box_id)
            return {"code": 1, "data": {"error": str(e), "server": host_name}}

        # run
        try:
            judger = Judger(run_config=language['run'],max_cpu_time=time_limit, max_memory=memory_limit,
                            test_case_id=test_case_id, box_id=box_id)
            result = judger.run()
            judge_result = {"result": RESULT["accepted"], "info": result,
                            "accepted_answer_time": None, "server": host_name}

            # for loop break and else
            for item in result:
                if item['status'] != RESULT['accepted']:
                    judge_result['result'] = item['status']
                    break
            else:
                # time = sorted(result, key=lambda k: k['time'])
                time = 0.0
                for item in result:
                    if item['time'] > time:
                        time = item['time']
                judge_result['accepted_answer_time'] = time
            remove_env(box_id)
            return {"code": 0, "data": judge_result}
        except Exception as e:
            remove_env(box_id)
            return {"code": 2, "data": {"error": str(e), "server": host_name}}
        finally:
            remove_env(box_id)

