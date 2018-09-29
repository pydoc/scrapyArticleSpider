
import requests
import time
from hashlib import sha1
import hmac
import base64
from PIL import Image
#定义类
class Zhihu(object):
    #构造器
    def __init__(self):
        self.session = requests.session()
        self.headers = {
            'Host':'www.zhihu.com',
            'Referer':'https://www.zhihu.com/question/29925879',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
        }
        self.session.headers.update(self.headers)
        self.picture=None
        self.signature=None
        self.picture_url=None
        pass

    #获取验证码方法，有时候不用获取验证码就可以直接登录
    def getcapture(self):
        message = self.session.get(url='https://www.zhihu.com/api/v3/oauth/captcha?lang=en').json()
        print(message)
        self.picture_url = self.session.put(url='https://www.zhihu.com/api/v3/oauth/captcha?lang=en').json()
        if message['show_captcha'] == False:
            self.picture=''
        else:
            #采用base64格式将验证码通过图片格式显示出来
            with open('验证码.jpg','wb') as f:
                f.write(base64.b64decode(self.picture_url['img_base64']))
            image = Image.open('验证码.jpg')
            image.show()
            self.picture = input('请输入验证码')
        time.sleep(2)
        message1 = self.session.post(url='https://www.zhihu.com/api/v3/oauth/captcha?lang=en',data={'input_text':self.picture}).json()
        print(message1)

    def get_signature(self):
        #知乎登陆的主要问题在于找到signature了这是重点。
        a = hmac.new('d1b964811afb40118a12068ff74a12f4'.encode('utf-8'), digestmod=sha1)
        a.update(b'password')
        a.update(b'c3cef7c66a1843f8b3a9e6a1e3160e20')
        a.update(b'com.zhihu.web')
        a.update(str(round(time.time() * 1000)).encode())
        self.signature = a.hexdigest()

    def Login_phone(self):
        data = {
            'client_id': 'c3cef7c66a1843f8b3a9e6a1e3160e20',
            'grant_type': 'password',
            'timestamp': str(int(time.time() * 1000)),
            'source': 'com.zhihu.web',
            'signature': self.signature,
            'username': '18801305865',
            'password': 'doc19921222',
            'captcha': self.picture,
            #'lang':'en',
            #'ref_source':'other_',
            #'utm_source':''
        }
        message = self.session.post(url='https://www.zhihu.com/api/v3/oauth/sign_in', headers=self.headers, data=data)
        message.encoding = 'utf-8'
        print(message.text)

    def target_url(self,url):
        resp = self.session.get(url)
        return resp.text

if __name__ == "__main__":
    zhihu=Zhihu()
    zhihu.getcapture()
    zhihu.get_signature()
    zhihu.Login_phone()
    print(zhihu.target_url('https://www.zhihu.com/'))

