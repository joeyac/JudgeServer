from __future__ import unicode_literals


class CompileError(Exception):
    pass


class JudgeServerError(Exception):
    pass


class SandboxError(Exception):
    pass


class VLoginFailed(Exception):
    pass


class VSubmitFailed(Exception):
    pass

