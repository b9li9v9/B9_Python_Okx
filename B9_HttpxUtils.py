import hmac
import base64
import datetime


def sign(message, secretKey):
    mac = hmac.new(bytes(secretKey, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    d = mac.digest()
    return base64.b64encode(d)


def pre_hash(timestamp, method, request_path, body):
    return str(timestamp) + str.upper(method) + request_path + body


def get_header(api_key, sign, timestamp, passphrase, flag):
    header = dict()
    header['Content-Type'] = 'application/json'
    header['OK-ACCESS-KEY'] = api_key
    header['OK-ACCESS-SIGN'] = sign
    header['OK-ACCESS-TIMESTAMP'] = str(timestamp)
    header[ 'OK-ACCESS-PASSPHRASE'] = passphrase
    if flag == '1':
        header['x-simulated-trading'] = flag
    # print('header: ',header)
    return header


def parse_params_to_str(params):
    url = '?'
    for key, value in params.items():
        url = url + str(key) + '=' + str(value) + '&'
    # print('url:',url)
    return url[0:-1]


def get_timestamp():
    now = datetime.datetime.utcnow()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"


def signature(timestamp, method, request_path, body, secret_key):
    if str(body) == '{}' or str(body) == 'None':
        body = ''
    message = str(timestamp) + str.upper(method) + request_path + str(body)

    mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    d = mac.digest()

    return base64.b64encode(d)
