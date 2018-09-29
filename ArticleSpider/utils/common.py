
import hashlib
import re


def get_md5(url):
    if isinstance(url, str):
        url = url.encode("utf-8")
    m = hashlib.md5()
    m.update(url)
    url_md5 = m.hexdigest()
    return url_md5


def extract_num(text):
    match_obj = re.match(".*?([,.\d]+).*", text)
    if match_obj:
        nums = int(match_obj.group(1).replace(",", ""))
    else:
        nums = 0
    return nums


if __name__ == "__main__":
    print(get_md5("https://www.lagou.com/jobs/5124162.html"))