# coding=utf-8
from __future__ import unicode_literals
from config import JUDGE_DEFAULT_PATH, TEST_CASE_DIR, TEST_CASE_IN_DIR_NAME
from utils import get_meta_info
import os
import commands


# isolate -p --cg-mem 256000 --cg -i input.data --run -- /usr/lib/jvm/java-9-oracle/bin/java -cp exe Main
# isolate -M meta.data -m 262144 -t 1 -w 3 -x 1 -b 1 -k 262144 -o output.data -r error.data -v --run -- ./Main
# isolate --cg --run /usr/bin/python3 a.py
# isolate --cg [mem_limit,kb] [time_limit,s,fractions allowed] [wall_time_limit,s,fractions allowed]
#                   [extra_time] [box_id]
#                   [output_limit,kb] [process_limit] [in,out,error] --run -- [run_args] [exe_file]


#   标准：
#   返回一个字典 {'status':status_code_defined,
#                 'info':detail}
#               detail:{'time': 0.000, (in seconds)
#                       'time-wall': 0.035, (in seconds)
#                       'max-rss': 1336, (in kilobytes)
#                       'csw-voluntary': 3,
#                       'csw-forced': 2,
#                       'exitcode': 1 (optional)
#                       'error': {string}
#                       }

class Runner(object):

    RESULT = {
        "success": 0,
        "runtime_error": 1,
        "time_limit_exceeded": 2,
        "memory_limit_exceeded": 3,
        "output_limit_exceeded": 4,

        "system_error": 5,
        "unknown_error": 6,
    }

    def __init__(self, max_cpu_time, max_real_time, max_memory, box_id,
                 max_output_size, max_process_number,
                 input_file, output_file, error_file, meta_file,
                 run_args,
                 input_file_dir=TEST_CASE_DIR,
                 group_memory=False
                 ):

        self.judge_dir = os.path.join(JUDGE_DEFAULT_PATH, box_id, 'box')

        self.max_cpu_time = max_cpu_time
        self.max_real_time = max_real_time
        self.max_memory = max_memory * 3
        self.box_id = box_id
        self.max_output_size = max_output_size * 2
        self.max_process_number = max_process_number
        self.input_file = input_file
        self.output_file = output_file
        self.error_file = error_file
        self.meta_file = meta_file
        self.run_args = run_args
        self.group_memory = group_memory
        self.input_file_dir = input_file_dir

        self.cmd_status = None
        self.cmd_result = None
        self.result = None

    def get_result(self):
        # meta file base:
        # time:0.000
        # time-wall:0.035
        # max-rss:1336
        # csw-voluntary:3
        # csw-forced:2
        result = {}
        error = ''
        error_file_path = os.path.join(JUDGE_DEFAULT_PATH, self.box_id, 'box', self.error_file)
        if os.path.exists(error_file_path):
            with open(error_file_path) as f:
                error = f.read().strip()

        if self.cmd_status == 0 or 256:
            meta = get_meta_info(self.meta_file)

            result['info'] = meta
            result['info']['error'] = error
            if 'exitcode' not in result['info']:
                result['info']['exitcode'] = 0

            output_file = os.path.join(JUDGE_DEFAULT_PATH, self.output_file)
            output_file_size = None
            if os.path.exists(output_file):
                output_file_size = float(os.path.getsize(output_file)) / 1024  # KB

            if output_file_size and output_file_size > self.max_output_size / 2:
                result['status'] = Runner.RESULT['output_limit_exceeded']

            if 'OK' in self.cmd_result:
                if meta['max-rss'] > self.max_memory / 3:
                    result['status'] = Runner.RESULT['memory_limit_exceeded']
                else:
                    result['status'] = Runner.RESULT['success']
            else:

                if meta['status'] == 'TO':
                    result['status'] = Runner.RESULT['time_limit_exceeded']
                elif meta['status'] == 'SG':
                    result['status'] = Runner.RESULT['runtime_error']
                elif meta['status'] == 'RE':
                    result['status'] = Runner.RESULT['runtime_error']
                else:  # meta[‘status’] == 'XX' — internal error of the sandbox
                    result['status'] = Runner.RESULT['system_error']

        else:
            result['status'] = Runner.RESULT['unknown_error']
            result['info']['error'] = error

        self.result = result

    def run(self):
        # Enable use of control groups.
        cmd = 'isolate --cg'

        # special sandbox id for used in parallel
        cmd += ' -b ' + str(self.box_id)

        # bind input data dir
        cmd += ' --dir=' + TEST_CASE_IN_DIR_NAME + '=' + str(self.input_file_dir)

        # Inherit all environment variables from the parent.
        cmd += ' -e'

        # memory limit like this because of JVM will create a process
        if self.group_memory:
            cmd += ' --cg-mem ' + str(self.max_memory)  # total memory limit
        else:
            cmd += ' -m ' + str(self.max_memory)  # every process memory limit

        cmd += ' -t ' + str(self.max_cpu_time)
        cmd += ' -w ' + str(self.max_real_time)

        # set extra time to report real execution time
        cmd += ' -x ' + str(1)

        if self.input_file:
            cmd += ' -i ' + os.path.join('/' + TEST_CASE_IN_DIR_NAME, self.input_file).encode("utf-8")

        cmd += ' -o ' + str(self.output_file)
        cmd += ' -r ' + str(self.error_file)

        cmd += ' -M ' + os.path.join(self.judge_dir, str(self.meta_file)).encode("utf-8")

        # cmd += ' -f ' + str(self.max_output_size)

        # Permit the program to create up to max processes and/or threads.
        cmd += ' -p'
        if self.max_process_number and self.max_process_number >= 1:
            cmd += '=' + str(self.max_process_number)

        cmd += ' --run -- '
        run_args = str(self.run_args)
        cmd += str(run_args)

        status, result = commands.getstatusoutput(cmd)
        self.cmd_status = status
        self.cmd_result = result
        self.get_result()
        # return status, result

        # print status
        # print result
        # return status
        # return time memory
