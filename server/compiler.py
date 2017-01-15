# coding=utf-8
from __future__ import unicode_literals
import sys
reload(sys) # Python2.5 初始化后会删除 sys.setdefaultencoding 这个方法，我们需要重新载入
sys.setdefaultencoding('utf-8')


import os
from config import JUDGE_DEFAULT_PATH ,DEBUG_COMPILER, DEBUG
from exception import SandboxError, CompileError
from _runner import Runner


def verify(box_id):
    try:
        box_id = int(box_id)
        if 0 <= box_id < 100:
            return True
    except:
        raise ValueError
    return False


# for isolate sandbox, compile c++,c need enable group control and set memory enough
class Compiler(object):
    def __init__(self, compile_config, box_id):
        self.compile_config = compile_config
        self.box_id = box_id

    def compile(self):
        if not verify(self.box_id):
            raise SandboxError('sandbox id should in range 0~99 ')

        # except meta file other are all relative path
        output_dir = os.path.join(JUDGE_DEFAULT_PATH, self.box_id, 'box')
        meta_file = os.path.join(output_dir, 'compiler.meta')

        compiler_out = 'compiler.out'

        command = self.compile_config["compile_command"]
        group_memory = self.compile_config.get('group_memory')
        command = command.format(src_name=self.compile_config['src_name'], exe_name=self.compile_config['exe_name'])
        compiler = Runner(max_cpu_time=self.compile_config['max_cpu_time'],
                          max_real_time=self.compile_config['max_real_time'],
                          max_memory=self.compile_config['max_memory'],
                          box_id=self.box_id,
                          max_output_size=1024,  # 1M
                          max_process_number=-1,
                          input_file=None,
                          output_file=compiler_out,
                          error_file=compiler_out,
                          meta_file=meta_file,
                          run_args=command,
                          group_memory=True if group_memory else False,
                          )
        compiler.run()
        if compiler.result['status'] == Runner.RESULT['success'] \
                or compiler.result['status'] == Runner.RESULT['memory_limit_exceeded']:
            return self.compile_config['exe_name']
        elif compiler.result['status'] == Runner.RESULT['system_error']:
            if DEBUG >> DEBUG_COMPILER & 1:
                print compiler.result
            info = compiler.result['info']
            raise SandboxError("info: %s" % str(info))
        else:
            if DEBUG >> DEBUG_COMPILER & 1:
                print compiler.result
            info = compiler.result['info']
            raise CompileError("info: %s" % str(info))

