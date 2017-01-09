# coding=utf-8
from __future__ import unicode_literals
import psutil
import os
import json
import hashlib

from multiprocessing import Pool

from config import TEST_CASE_DIR, JUDGER_RUN_LOG_PATH, JUDGE_DEFAULT_PATH
from utils import replace_blank
from _runner import Runner
from result import RESULT
from config import DEBUG

from exception import JudgeServerError


# 下面这个函数作为代理访问实例变量，否则Python2会报错，是Python2的已知问题
# http://stackoverflow.com/questions/1816958/cant-pickle-type-instancemethod-when-using-pythons-multiprocessing-pool-ma/7309686
def _run(instance, test_file_info):
    return instance._judge_one(test_file_info)


class Judger(object):
    def __init__(self, run_config, max_cpu_time, max_memory, test_case_id, box_id):
        self.run_config = run_config
        self.max_cpu_time = max_cpu_time
        self.max_memory = max_memory
        self.test_case_id = test_case_id
        self.exe_name = run_config['exe_name']
        self.box_id = box_id

        self.test_case_dir = os.path.join(TEST_CASE_DIR, test_case_id)
        self.out_put_dir = os.path.join(JUDGE_DEFAULT_PATH, box_id, 'box')
        self.test_case_info = self._load_test_case_info()
        self.pool = Pool(processes=psutil.cpu_count())

    def _load_test_case_info(self):
        try:
            with open(os.path.join(self.test_case_dir, "info")) as f:
                return json.loads(f.read())
        except IOError:
            raise JudgeServerError('Test case not found')
        except ValueError:
            raise JudgeServerError('Bad test case config')

    def _compare_output(self, out_file_name):
        user_output_file_path = os.path.join(self.out_put_dir, out_file_name)

        stand_output_file_path = os.path.join(self.test_case_dir, out_file_name)
        strip_output_file_path = os.path.join(self.test_case_dir,  out_file_name + '.strip')
        end_strip_output_file_path = os.path.join(self.test_case_dir,  out_file_name + '.end.strip')

        # check if the same without space,tab,and enter
        if os.path.exists(strip_output_file_path):
            with open(strip_output_file_path, "r") as f:
                content = f.read()
            strip_output_md5 = content
        else:
            with open(stand_output_file_path, "r") as f:
                content = f.read()
            strip_output_md5 = hashlib.md5(replace_blank(content)).hexdigest()
            with open(strip_output_file_path, "w") as f:
                f.write(strip_output_md5)

        with open(user_output_file_path, "r") as f:
            content = f.read()
        user_strip_output_md5 = hashlib.md5(replace_blank(content)).hexdigest()

        result_strip = strip_output_md5 == user_strip_output_md5

        # check if the same without end_line space
        if os.path.exists(end_strip_output_file_path):
            with open(end_strip_output_file_path, "r") as f:
                content = f.read()
            end_strip_output_md5 = content
        else:
            with open(stand_output_file_path, "r") as f:
                content = f.read()
            end_strip_output_md5 = hashlib.md5(content.rstrip()).hexdigest()
            with open(end_strip_output_file_path, "w") as f:
                f.write(end_strip_output_md5)

        with open(user_output_file_path, "r") as f:
            content = f.read()
        user_end_strip_output_md5 = hashlib.md5(content.rstrip()).hexdigest()

        result = end_strip_output_md5 == user_end_strip_output_md5

        # 0 AC 1 PE -1 WA
        if result_strip:
            if result:
                return 0
            else:
                return 1
        return -1

    def _judge_one(self, test_file_info):
        input_file = test_file_info['in']
        user_out_file_name = test_file_info['out']
        command = self.run_config['command'].format(exe_name=self.exe_name)
        group_memory = self.run_config.get('group_memory')
        max_output_size = self.run_config.get('max_output_size')

        output_dir = os.path.join(JUDGE_DEFAULT_PATH, self.box_id, 'box')
        meta_file = os.path.join(output_dir, 'judger.meta')
        judge_error = 'judger.error'

        judger = Runner(max_cpu_time=self.max_cpu_time,
                        max_real_time=self.max_cpu_time*3,
                        max_memory=self.max_memory,
                        box_id=self.box_id,
                        max_output_size=max_output_size if max_output_size else 1024*1024,  # 1G 输出文件最大不可能超过1G 否则输出OLE
                        max_process_number=-1,
                        input_file=input_file,
                        output_file=user_out_file_name,
                        error_file=judge_error,
                        meta_file=meta_file,
                        run_args=command,
                        group_memory=True if group_memory else False,
                        input_file_dir=os.path.join(TEST_CASE_DIR, self.test_case_id)
                        )
        judger.run()
        run_result = judger.result
        run_result['test_case'] = input_file
        if run_result['status'] == Runner.RESULT['success']:  # run compare
            # 0 AC 1 PE -1 WA
            signer = self._compare_output(out_file_name=user_out_file_name)
            if not signer:
                run_result['status'] = RESULT['accepted']
            elif signer == 1:
                run_result['status'] = RESULT['presentation_error']
            else:
                run_result['status'] = RESULT['wrong_answer']
        else:
            if run_result['status'] == Runner.RESULT['time_limit_exceeded'] or Runner.RESULT['memory_limit_exceeded']:
                pass
            elif run_result['status'] == Runner.RESULT['floating_point_exception']:
                run_result['status'] = RESULT['runtime_error']
                run_result['info'] = 'floating_point_exception'
            elif run_result['status'] == Runner.RESULT['unknown_error'] or Runner.RESULT['runtime_error']:
                run_result['status'] = RESULT['runtime_error']
            else:
                run_result['status'] = RESULT['system_error']
        return run_result

    def run(self):
        # 添加到任务队列
        tmp_results = []
        results = []
        for case_id, info in self.test_case_info.iteritems():
            if DEBUG:
                print 'run the '+ str(case_id) + ' test case...'
            tmp_results.append(self.pool.apply_async(_run, (self, info)))
        self.pool.close()
        self.pool.join()
        for item in tmp_results:
            # exception will be raised, when get() is called
            # # http://stackoverflow.com/questions/22094852/how-to-catch-exceptions-in-workers-in-multiprocessing
            results.append(item.get())
        return results

    def __getstate__(self):
        # 不同的pool之间进行pickle的时候要排除自己，否则报错
        # http://stackoverflow.com/questions/25382455/python-notimplementederror-pool-objects-cannot-be-passed-between-processes
        self_dict = self.__dict__.copy()
        del self_dict['pool']
        return self_dict
