import json

from pywss import Pyws, route, AuthenticationError, ConnectManager, ERROR_FLAG, \
    DaemonMiddleware, DataMiddleware


class AuthenticationMiddleware(DaemonMiddleware):
    """
    该中间件仅一次起作用，可以用于首次连接时的验证
    返回值有两种类型:
    第一种: string，用于作为连接者的名字
    第二种: tuple，第二参数用于指定用户退出时的清除级别
    """

    @classmethod
    def process_input(self, request, input_msg):
        json_data = json.loads(input_msg)
        if 'name' in json_data:
            return str(json_data['name']), 1
        raise AuthenticationError


class DataProcessMiddleware(DataMiddleware):
    """
    每一次数据传进来时都会进行处理
    可以用作对常见数据进行处理
    """

    @classmethod
    def process_input(cls, request, input_msg):
        return json.loads(input_msg)


@route('/test/example/2')
def example_2(request, data):
    if 'name' in data and 'msg' in data:
        if ConnectManager.exists(data['name']):
            ConnectManager.send_to_connector(data['name'], data['msg'])
            msg = {'state': 1, 'msg': 'success'}
        else:
            msg = {'state': 0, 'msg': '用户不存在或系统内部异常'}
    else:
        request.ws_send({'state': 0, 'msg': '请求数据参数错误'})
        msg = ERROR_FLAG
    return msg


if __name__ == '__main__':
    ws = Pyws(__name__, address='127.0.0.1', port=8866)
    ws.add_middleware([AuthenticationMiddleware, DataProcessMiddleware])
    ws.serve_forever()

"""
/* Client1 Code */
ws1 = new WebSocket("ws://127.0.0.1:8866/test/example/2");
ws1.onmessage = function (ev) {
    console.log(JSON.parse(ev.data));
}
ws1.onclose = function (ev) {
    console.log('Connect Closed')
}
ws1.onopen = function() {
    if (ws1.readyState === WebSocket.OPEN) {
        ws1.send(JSON.stringify({'name': 'test1'}))  // you will get enter the AuthenticationMiddleware first
    }
}

/* Client2 Code */
ws2 = new WebSocket("ws://127.0.0.1:8866/test/example/2");
ws2.onmessage = function (ev) {
    console.log(JSON.parse(ev.data));
}
ws2.onclose = function (ev) {
    console.log('Connect Closed')
}
ws2.onopen = function() {
    if (ws2.readyState === WebSocket.OPEN) {
        ws2.send(JSON.stringify({'name': 'test2'}))  // you will get enter the AuthenticationMiddleware first
    }
}

/* other */
ws1.send(JSON.stringify({'name': 'test2', 'msg': 'hai, test2, how are you?'}))
ws2.send(JSON.stringify({'name': 'test1', 'msg': '???stupid???'}))
"""
