# coding=utf-8
from __future__ import unicode_literals

import hashlib
import json

import requests


class JudgeServerClientError(Exception):
    pass


class JudgeServerClient(object):
    def __init__(self, token, server_base_url):
        self.token = hashlib.sha256(token).hexdigest()
        self.server_base_url = server_base_url.rstrip("/")

    def _request(self, url, data=None):
        headers= {"Authorization": 'Token ' + self.token,
                  "Content-Type": "application/json"}
        try:
            if data:
                print '------------'
                print url
                print self.token
                print data
                print '------------'
                return requests.post(url, headers=headers, json=data).json()
            else:
                return requests.get(url, headers=headers).json()
        except Exception as e:
            raise JudgeServerClientError(e.message)

    def ping(self):
        return self._request(self.server_base_url + '/ping/')

    def judge(self, submission_id, language_code, src, time_limit, memory_limit, test_case_id):
        data ={
            'submission_id': submission_id,
            'language_code': language_code,
            'time_limit': time_limit,  # ms
            'memory_limit': memory_limit,  # kb
            'test_case_id': test_case_id,
            'code': src,
        }
        return self._request(self.server_base_url + "/judge/", data=data)


if __name__ == "__main__":
    c_src = r"""
    #include <stdio.h>
    int main(){
        int a, b;
        scanf("%d%d", &a, &b);
        printf("%d\n", a+b);
        return 0;
    }
    """

    cpp_src = r"""
    #include <iostream>

    using namespace std;

    int main()
    {
        int a,b;
        cin >> a >> b;
        cout << a+b << endl;
        return 0;
    }
    """

    java_src = r"""
    import java.util.Scanner;
    public class Main{
        public static void main(String[] args){
            Scanner in=new Scanner(System.in);
            int a=in.nextInt();
            int b=in.nextInt();
            System.out.println(a + b);
        }
    }
    """

    py2_src = """s = raw_input()
s1 = s.split(" ")
print int(s1[0]) + int(s1[1])"""

    client = JudgeServerClient(token="token", server_base_url="http://172.17.0.2:8080/")
    print client.ping(), "\n\n"
    x = raw_input('press enter to continue...')
    print client.judge(src=c_src,submission_id='c',language_code=1,time_limit=1000,memory_limit=64*1024,
                       test_case_id='b',), "\n\n"
    x = raw_input('press enter to continue...')
    print client.judge(src=cpp_src,submission_id='c++',language_code=2,time_limit=1000,memory_limit=64*1024,
                       test_case_id='b',), "\n\n"
    x = raw_input('press enter to continue...')
    print client.judge(src=py2_src,submission_id='python2',language_code=4,time_limit=1000,memory_limit=64*1024,
                       test_case_id='b',), "\n\n"
    x = raw_input('press enter to continue...')
    print client.judge(src=java_src,submission_id='java',language_code=3,time_limit=1000,memory_limit=128*1024,
                       test_case_id='b',), "\n\n"
    x = raw_input('press enter to continue...')