"""微信 iLink Bot 直连 API 发送脚本
替代 MCP 发送（避免 context_token 失效导致静默丢弃）。
发送前自动预热，text/image 共用同一 context_token。
"""
import json, urllib.request, ssl, time, sys, os

ACC = 'C:/Users/DawnCloud/.claude/channels/wechat/account.json'
CTX = 'C:/Users/DawnCloud/.claude/channels/wechat/context_tokens.json'


def _load_auth():
    with open(ACC) as f:
        acct = json.load(f)
    with open(CTX) as f:
        ctx = json.load(f)
    uid = list(ctx.keys())[0]
    return acct, ctx, uid


def _api_post(body):
    acct, ctx, uid = _load_auth()
    # 确保 context_token 是最新的
    body['msg']['context_token'] = ctx[uid]
    # 注入必要字段
    body['msg']['to_user_id'] = uid
    body['msg']['from_user_id'] = ''
    body['msg'].setdefault('client_id', f'claude-{int(time.time() * 1000)}')
    body['msg'].setdefault('message_type', 2)
    body['msg'].setdefault('message_state', 2)
    body.setdefault('base_info', {'channel_version': '0.3.0'})

    data = json.dumps(body).encode()
    req = urllib.request.Request(
        'https://ilinkai.weixin.qq.com/ilink/bot/sendmessage',
        data=data, method='POST',
    )
    req.add_header('Content-Type', 'application/json')
    req.add_header('AuthorizationType', 'ilink_bot_token')
    req.add_header('Authorization', 'Bearer ' + acct['token'])
    resp = urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=30)
    return resp.status, resp.read().decode()


def send_text(text: str) -> bool:
    """发送文本消息。自动使用最新 context_token，无需预热。"""
    body = {
        'msg': {
            'item_list': [{'type': 1, 'text_item': {'text': text}}],
        }
    }
    try:
        status, resp = _api_post(body)
        ok = status == 200
        print(f"WECHAT_TEXT {'OK' if ok else 'FAIL'}: HTTP {status}")
        if not ok:
            print(f"  Response: {resp[:200]}")
        return ok
    except Exception as e:
        print(f"WECHAT_TEXT FAIL: {e}")
        return False


def send_image(image_path: str) -> bool:
    """发送图片消息。
    iLink Bot 不支持直接内嵌图片（需先上传 CDN 拿 cdn_attachid）。
    故此函数直接返回 False 触发 MCP 降级。
    """
    abs_path = os.path.abspath(image_path)
    if not os.path.exists(abs_path):
        print(f"WECHAT_IMAGE FAIL: 文件不存在 - {abs_path}")
        return False

    # iLink Bot 图片发送需先调用 upload 接口获取 cdn_attachid/aeskey/md5，
    # 再通过 image_item 引用。upload 接口尚未逆向。
    # 直接降级 MCP。
    print("WECHAT_IMAGE: 直连 API 不支持内嵌图片，降级 MCP（调用方负责）")
    return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python wechat_send.py text <message>")
        print("       python wechat_send.py image <path>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == 'text':
        msg = sys.argv[2] if len(sys.argv) > 2 else ''
        ok = send_text(msg)
    elif cmd == 'image':
        path = sys.argv[2] if len(sys.argv) > 2 else ''
        ok = send_image(path)
    else:
        print(f"Unknown command: {cmd}")
        ok = False

    sys.exit(0 if ok else 1)
