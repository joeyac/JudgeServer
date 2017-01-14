# coding=utf-8
from __future__ import unicode_literals
languages = {
    1: {
        'name': 'c',
        'compile': {
            "group_memory": True,
            "src_name": "main.c",
            "exe_name": "main",
            "max_cpu_time": 5.0,
            "max_real_time": 10.0,
            "max_memory": 512 * 1024,  # 512M compile memory
            "compile_command": "/usr/bin/gcc -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c99 {src_name} -lm -o {exe_name}",
        },
        "run": {
            "exe_name": "main",
            "command": "./{exe_name}",
        }
    },
    2: {
        "name": "c++",
        "compile": {
            "group_memory": True,
            "src_name": "main.cpp",
            "exe_name": "main",
            "max_cpu_time": 5.0,
            "max_real_time": 10.0,
            "max_memory": 512 * 1024,  # 512M compile memory
            "compile_command": "/usr/bin/g++ -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c++11 {src_name} -lm -o {exe_name}",
        },
        "run": {
            "exe_name": "main",
            "command": "{exe_name}",
        }
    },
    3: {
        "name": "java",
        "compile": {
            "group_memory": True,
            "src_name": "Main.java",
            "exe_name": "Main",
            "max_cpu_time": 3.0,
            "max_real_time": 5.0,
            "max_memory": 512 * 1024,
            "compile_command": "/usr/lib/jvm/java-9-oracle/bin/javac {src_name} -d {exe_name} -encoding UTF8"
        },
        "run": {
            "group_memory": True,
            "exe_name": "Main",
            "command": "/usr/lib/jvm/java-9-oracle/bin/java -cp {exe_name}  Main",
        }
    },
    4: {
        "name": "python2",
        "compile": {
            "group_memory": True,
            "src_name": "solution.py",
            "exe_name": "solution.pyc",
            "max_cpu_time": 3000,
            "max_real_time": 5000,
            "max_memory": 128 * 1024,
            "compile_command": "/usr/bin/python -m py_compile {src_name}",
        },
        "run": {
            "exe_name": "solution.pyc",
            "command": "/usr/bin/python {exe_name}",
        }
    },
    5: {
        "name": "python3",
        "compile": {
            "group_memory": True,
            "src_name": "solution.py",
            "exe_name": "solution.py",
            "max_cpu_time": 3000,
            "max_real_time": 5000,
            "max_memory": 128 * 1024,
            "compile_command": "/usr/bin/python3 -m py_compile {src_name}",
        },
        "run": {
            "exe_name": "solution.py",
            "command": "/usr/bin/python3 {exe_name}",
        }
    }
}