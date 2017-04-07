# coding=utf-8
from __future__ import unicode_literals
import hashlib
import requests


class JudgeServerClientError(Exception):
    pass


class JudgeServerClient(object):
    def __init__(self, token, server_base_url):
        self.token = hashlib.sha256(token).hexdigest()
        # 3c469e9d6c5875d37a43f353d4f88e61fcf812c66eee3457465a40b0da4153e0
        self.server_base_url = server_base_url.rstrip("/")

    def _request(self, url, data=None, files=None):
        headers = {"Authorization": 'Token ' + self.token,
                   "Content-Type": "application/json"}
        try:
            if data:
                print '------------'
                print url
                print self.token
                print data
                print '------------'
                if files:
                    return requests.post(url, headers=headers, data=data, files=files).json()
                else:
                    return requests.post(url, headers=headers, json=data, files=files).json()
            else:
                return requests.get(url, headers=headers).json()
        except Exception as e:
            raise JudgeServerClientError(e.message)

    def ping(self):
        return self._request(self.server_base_url + '/ping/')

    def judge(self, submission_id, language_name, src_code, time_limit, memory_limit, test_case_id):
        data ={
            'submission_id': submission_id,
            'language_name': language_name,
            'src_code': src_code,

            'time_limit': time_limit,  # ms
            'memory_limit': memory_limit,  # kb
            'test_case_id': test_case_id,

        }
        return self._request(self.server_base_url + "/judge/", data=data)

    def vjudge(self, oj, problem_id, language_name, src_code, submission_id):
        data = {
            'submission_id': submission_id,
            'language_name': language_name,
            'src_code': src_code,

            'oj': oj,
            'problem_id': problem_id,
        }
        return self._request(self.server_base_url + '/vjudge/', data=data)

    def hash(self, test_case_id):
        data = {
            'test_case_id': test_case_id,
        }
        return self._request(self.server_base_url + "/hash/", data=data)

    def sync(self, test_case_id, file_path):
        # TODO
        # 该方法只适用于上传小文件，上传大文件的时候就需要用到流式上传，否则占用主机内存太多。
        # 参考文档http://docs.python-requests.org/zh_CN/latest/user/advanced.html#advanced。
        data = {'test_case_id': test_case_id, }
        files = {'file': open(file_path, 'rb')}
        return self._request(self.server_base_url + "/sync/", data=data, files=files)

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
    const int maxn=3e3+1;
    int c[maxn];
    int main()
    {
        int a,b;
        for(int i=0;i<maxn;i++)c[i]=1;
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

    py3_src = """s = input()
s1 = s.split(" ")
print(int(s1[0]) + int(s1[1]))"""

    # client = JudgeServerClient(token="token", server_base_url="http://172.17.0.2:8080/")
    client = JudgeServerClient(token="token", server_base_url="http://localhost:5000/")
    # print client.hash('a+b')
    path = '/home/rhyme/code/DEV/oj-master/test_case/a+b_problem/a+b_problem.zip'
    token = hashlib.sha256("token").hexdigest()
    headers = {"Authorization": 'Token ' + token}
    data = {'test_case_id': 'a+b'}
    files = {'zipfile': open(path, 'rb')}
    import json
    # res = requests.post("http://localhost:5000/sync/", headers=headers, data=data, files=files)
    res = requests.get("http://localhost:5000/ping/", headers=headers)
    print res.headers
    print res.json()
    # x = open('json.data', 'a')
    # import json
    # x.write(json.dumps(client.ping()))
    # x.write(str('\n\n'))
    #
    # print client.ping(), "\n\n"
    # y = raw_input('press enter to continue...')
    # q = client.judge(src_code=c_src,submission_id=123, language_name='c', time_limit=10000,memory_limit=64*1024,
    #                  test_case_id='b',)
    # x.write(json.dumps(q))



    # x = raw_input('press enter to continue...')
    # print client.judge(src=cpp_src,submission_id='c++', language_name='c++',time_limit=10000,memory_limit=64*1024,
    #                    test_case_id='b',), "\n\n"
    # x = raw_input('press enter to continue...')
    # print client.judge(src=py2_src,submission_id='python2', language_name='python2',time_limit=1000,memory_limit=64*1024,
    #                    test_case_id='b',), "\n\n"
    # x = raw_input('press enter to continue...')
    # print client.judge(src=py3_src,submission_id='python3', language_name='python3',time_limit=1000,memory_limit=64*1024,
    #                    test_case_id='b',), "\n\n"
    # x = raw_input('press enter to continue...')
    # print client.judge(src=java_src,submission_id='java', language_name='java',time_limit=1000,memory_limit=128*1024,
    #                    test_case_id='b',), "\n\n"
    # x = raw_input('press enter to continue...')
    # print client.vjudge(1, 1000, 'g++', cpp_src, 29)
