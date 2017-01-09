# coding=utf-8
from __future__ import unicode_literals
import psutil
import socket
import logging
import os
import commands
import hashlib
import shutil

from config import TOKEN_FILE_PATH, LOG_BASE, BASE_PATH, JUDGE_DEFAULT_PATH, DEBUG
from exception import SandboxError,JudgeServerError

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(threadName)s:%(thread)d] [%(name)s:%(lineno)d]'
                           ' [%(module)s:%(funcName)s] [%(levelname)s]- %(message)s',
                    filename='log/judge.log')

logger = logging


def server_info():
    cmd = 'isolate --version'
    (exit_status, out_text) = commands.getstatusoutput(cmd)
    if exit_status != 0:
        raise SandboxError("isolate(https://github.com/ioi/isolate) not found or error")
    return {"hostname": socket.gethostname(),
            "cpu": psutil.cpu_percent(),
            "cpu_core": psutil.cpu_count(),
            "memory": psutil.virtual_memory().percent,
            "judger_version": out_text,
            }


def get_token():
    try:
        with open(TOKEN_FILE_PATH, "r") as f:
            return f.read().strip()
    except IOError:
        raise JudgeServerError("token.txt not found")


def interpret(val):
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val


def get_meta_info(file_path):
    try:
        result = {}
        with open(file_path) as f:
            for line in f:
                name, var = line.partition(':')[::2]
                result[name.strip()] = interpret(var.strip())
            return result
    except IOError:
        raise JudgeServerError("meta file not found")
    except ValueError:
        raise JudgeServerError("Bad meta file config")


def replace_blank(string):
    return string.replace('\t', '').replace('\n', '').replace(' ', '')


def choose_box_id():
    for box_id in range(100):
        path = os.path.join(JUDGE_DEFAULT_PATH, str(box_id))
        if not os.path.exists(path):
            return str(box_id)
    return None


class InitIsolateEnv(object):
    def __init__(self):
        self.box_id = choose_box_id()

    def __enter__(self):
        if not self.box_id:
            raise JudgeServerError("failed to get box id")
        try:
            cmd = 'isolate -b {box_id} --cg --init'
            cmd = cmd.format(box_id=self.box_id)
            status, result = commands.getstatusoutput(cmd)
            if DEBUG:
                print cmd
            if status != 0:
                raise JudgeServerError("failed to create runtime dir")
        except Exception as e:
            logger.exception(e)
            raise JudgeServerError("failed to create runtime dir")
        return self.box_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            cmd = 'isolate -b {box_id} --cleanup'
            cmd = cmd.format(box_id=self.box_id)
            status, result = commands.getstatusoutput(cmd)
            path = os.path.join(JUDGE_DEFAULT_PATH, self.box_id)  # prevent for unclean
            if os.path.exists(path):
                shutil.rmtree(path)
            if DEBUG:
                print cmd, status
            if os.path.exists(path):
                raise JudgeServerError("failed to clean runtime dir")
        except Exception as e:
            logger.exception(e)
            raise JudgeServerError("failed to clean runtime dir")

token = hashlib.sha256(get_token()).hexdigest()
