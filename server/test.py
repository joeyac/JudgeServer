import os
import hashlib
import json
import sys
sys.path.append("..")
# s=os.path.join('test')
# print s
# print os.getcwd()
from client.languages import cpp_lang_config, c_lang_config, java_lang_config
from config import BASE_PATH, JUDGE_DEFAULT_PATH, TEST_CASE_DIR
from exception import JudgeServerError
import commands


def interpret(val):
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val


def TT():
        def get_file_info():
                try:
                        result = {}
                        with open(os.path.join(BASE_PATH, "meta.data")) as f:
                                for line in f:
                                        name, var = line.partition(':')[::2]
                                        result[name.strip()] = interpret(var.strip())
                                return result
                except IOError:
                        raise JudgeServerError("Test case not found")
                except ValueError:
                        raise JudgeServerError("Bad test case config")
        x = get_file_info()
        if x['csw-forced']==45:
                print 'fuck u'
        for a, b in x.iteritems():
                print a+"___"+str(b)


def get_hash():
        x = 'a+b problem'
        token = hashlib.sha256(x).hexdigest()
        # 9386c61e9a8001efa9fc4f875410419fa42f4eff9c13c3ed81382514518ce157
        print token

def test():
        from compiler import Compiler
        box_id = 0
        src_name = 'a.c'
        src_path = src_name  # except meta file other are all relative path
        com = Compiler(cpp_lang_config['compile'], str(box_id))
        print com.compile
# isolate --cg -b 0 -e -r errorc.data --cg-mem 300000 -M meta.out --processes --run -- /usr/bin/g++ -O2 -w -std=c++11 a.cpp -lm -o a.o
# isolate --cg -b 0 -e --dir=data/=/home/rhyme/code/USTBJudgeServer/JudgeServer/server/test_case/a
# -i data/1.in -o out.out -r error.out  -m 10240 -M meta.out --processes --run -- a.o
# TT()
# print ''
# test()

#
def _load_test_case_info():
    try:
        with open(os.path.join(TEST_CASE_DIR, 'a', "info")) as f:
            return json.loads(f.read())
    except IOError:
        raise JudgeServerError("Test case not found")
    except ValueError:
        raise JudgeServerError("Bad test case config")

x = _load_test_case_info()
# count = x['count']
# for i in range(1,count+1):
#     print x[str(i)]
for test_case_file_id, _ in x.iteritems():
    print test_case_file_id
    print _
    print 'down'


def dev_test():
    cmd1 = 'g++ /var/local/lib/isolate/3/box/a.cpp -w -std=c++11 -lm -o /var/local/lib/isolate/3/box/a.o'
    cmd2 = 'isolate -b 3 --cg -p -t 3 -m 30240 -f 1 ' \
           '-M run.meta -r run.error -i data.in -o run.out -v -v -v --run -- ./a.o'
    cmd3 = 'isolate -b 3 -t 3 -m 40240 -f 1 ' \
           '-M run.meta -r run.error -i data.in -o run.out -v -v -v --run -- ./a.o'
    (status, result) = commands.getstatusoutput(cmd1)
    print status, result
    x = raw_input('press enter to continue...')
    (status, result) = commands.getstatusoutput(cmd2)
    print status, result
    x = raw_input('press enter to continue...')
    (status, result) = commands.getstatusoutput(cmd3)
    print status, result
    x = raw_input('press enter to continue...')

def rm_box():
    cmd = 'isolate -b {box_id} --cleanup'
    for id in range(1,27):
        run = cmd.format(box_id=id)
        status, result = commands.getstatusoutput(cmd)
        print result, id

# _load_test_case_info()
rm_box()