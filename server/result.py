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

RE_RESULT = {
     0: "accepted",

     1: "runtime error",
     2: "time limit exceeded",
     3: "memory limit exceeded",

     4: "output limit exceeded",

     5: "compile error",

     6: "presentation error",
     7: "wrong answer",
}
