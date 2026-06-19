"""WeChat iLink Bot 会话预热脚本
在 MCP 微信发送前调用，防止 context_token 失效导致消息静默丢弃。
"""
import json, urllib.request, ssl, time, sys, os

ACC = os.path.join(os.path.expanduser('~'), '.claude', 'channels', 'wechat', 'account.json')
CTX = os.path.join(os.path.expanduser('~'), '.claude', 'channels', 'wechat', 'context_tokens.json')

def warmup():
    try:
        with open(ACC) as f:
            acct = json.load(f)
        with open(CTX) as f:
            ctx = json.load(f)

        if not ctx:
            print("WARMUP_SKIP: context_tokens.json 为空，请先从微信给 bot 发一条消息")
            return True  # 不阻塞，让 MCP 自行处理

        uid = list(ctx.keys())[0]
        body = json.dumps({
            'msg': {
                'from_user_id': '',
                'to_user_id': uid,
                'client_id': f'warmup-{int(time.time() * 1000)}',
                'message_type': 2,
                'message_state': 2,
                'item_list': [{'type': 1, 'text_item': {'text': 'CC'}}],
                'context_token': ctx[uid],
            },
            'base_info': {'channel_version': '0.3.0'},
        }).encode()

        req = urllib.request.Request(
            'https://ilinkai.weixin.qq.com/ilink/bot/sendmessage',
            data=body, method='POST',
        )
        req.add_header('Content-Type', 'application/json')
        req.add_header('AuthorizationType', 'ilink_bot_token')
        req.add_header('Authorization', 'Bearer ' + acct['token'])

        resp = urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=10)
        print(f"WARMUP_OK: HTTP {resp.status}")
        return True

    except FileNotFoundError as e:
        print(f"WARMUP_FAIL: 缺少凭证文件 - {e}")
        return False
    except Exception as e:
        print(f"WARMUP_FAIL: {e}")
        return False

if __name__ == '__main__':
    ok = warmup()
    sys.exit(0 if ok else 1)
