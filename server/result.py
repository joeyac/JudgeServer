# coding=utf-8

RESULT = {
    "accepted": 0,

    "runtime_error": 1,  # runner
    "time_limit_exceed": 2,
    "memory_limit_exceed": 3,
    "output_limit_exceed": 4,

    "compile_error": 5,  # compiler

    "presentation_error": 6,  # judger
    "wrong_answer": 7,

    "system_error": 8,  # extra
    "waiting": 9,
}

# 这个映射关系是前后端通用的,判题服务器提供接口,也应该遵守这个,可能需要一些转换