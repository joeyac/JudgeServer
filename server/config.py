# coding=utf-8
from __future__ import unicode_literals
import os

DEBUG = True

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
