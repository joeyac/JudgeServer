# coding=utf-8
from __future__ import unicode_literals

c_lang_config = {
    "name": "c",
    "compile": {
        "group_memory": True,
        "src_name": "main.c",
        "exe_name": "main",
        "max_cpu_time": 5.0,
        "max_real_time": 10.0,
        "max_memory": 512 * 1024,  # 512M compile memory
        "compile_command": "/usr/bin/gcc -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c99 {src_path} -lm -o {exe_path}",
    },
    "run": {
        "exe_name": "main",
        "max_cpu_time": 1.0,
        "max_real_time": 5.0,
        "max_memory": 10 * 1024,  # 10M compile memory
        "command": "{exe_path}",
    }
}

cpp_lang_config = {
    "name": "c++",
    "compile": {
        "group_memory": True,
        "src_name": "main.cpp",
        "exe_name": "main",
        "max_cpu_time": 5.0,
        "max_real_time": 10.0,
        "max_memory": 512 * 1024,  # 512M compile memory
        "compile_command": "/usr/bin/g++ -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c++11 {src_path} -lm -o {exe_path}",
    },
    "run": {
        "exe_name": "main",
        "max_cpu_time": 1.0,
        "max_real_time": 5.0,
        "max_memory": 10 * 1024,  # 10M compile memory
        "command": "{exe_path}",
    }
}

java_lang_config = {
    "name": "java",
    "compile": {
        "group_memory": True,
        "src_name": "Main.java",
        "exe_name": "Main",
        "max_cpu_time": 3.0,
        "max_real_time": 5.0,
        "max_memory": -1,
        "compile_command": "/usr/bin/javac {src_path} -d {exe_name} -encoding UTF8"
    },
    "run": {
        "group_memory": True,
        "exe_name": "Main",
        "max_cpu_time": 1.0,
        "max_real_time": 5.0,
        "max_memory": 10 * 1024,  # 10M compile memory
        "command": "/usr/bin/java -cp {exe_name}  Main",
    }
}


py2_lang_config = {
    "name": "python2",
    "compile": {
        "src_name": "solution.py",
        "exe_name": "solution.pyc",
        "max_cpu_time": 3000,
        "max_real_time": 5000,
        "max_memory": 128 * 1024 ,
        "compile_command": "/usr/bin/python -m py_compile {src_path}",
    },
    "run": {
        "exe_name": "solution.pyc",
        "command": "/usr/bin/python {exe_path}",
    }
}