# coding=utf-8
import SocketServer
from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from solve import JudgeServer


class AsyncXMLRPCServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer):
    pass


server = AsyncXMLRPCServer(('0.0.0.0', 8080), SimpleXMLRPCRequestHandler, allow_none=True)
server.register_instance(JudgeServer())
server.serve_forever()