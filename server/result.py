# coding=utf-8


# 这个映射关系是前后端通用的,判题服务器提供接口,也应该遵守这个,可能需要一些转换
RESULT = {
    "accepted": 0,
    "runtime_error": 1,
    "time_limit_exceeded": 2,
    "memory_limit_exceeded": 3,
    "compile_error": 4,
    "presentation_error": 5,
    "wrong_answer": 6,
    "system_error": 7,
    "waiting": 8
}

# class Runner(object):
#     RESULT = {
#         "success": 0,
#         "runtime_error": 1,
#         "time_limit_exceeded": 2,
#         "memory_limit_exceeded": 3,
#         "system_error": 7,
#         "floating_point_exception": 8,
#         "unknown_error": 9,
#     }