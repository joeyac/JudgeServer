# coding=utf-8
from __future__ import unicode_literals
import os

# SET debug to a number range[0,16)
DEBUG = 15

DEBUG_RUNNER = 0
DEBUG_COMPILER = 1
DEBUG_JUDGER = 2
DEBUG_API = 3
# debug number:
# binary X|X|X|X
# runner|compiler|judger|api

REMOTE_DEBUG = False
# show the crawler and submitter info

BASE_PATH = os.getcwd()

TOKEN_FILE_PATH = os.path.join(BASE_PATH, "token.txt")
TEST_CASE_DIR = os.path.join(BASE_PATH, "test_case")

JUDGE_DEFAULT_PATH = '/var/local/lib/isolate/'

# we need redirect stand input to data.in,but do not want user code get data.out,
# so set this to a random variable so that the test_case dir in sandbox can not be access by user code
TEST_CASE_IN_DIR_NAME = 'aoinmw3qjr3qeqq3'

# TLE MLE OLE WA PE AC RE CE UE
# time limit exceed
# memory limit exceed
# output limit exceed
# wrong answer
# presentation error
# accepted
# runtime error
# compile error [checked c++
# unknown error
# judging
