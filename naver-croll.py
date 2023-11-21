import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from bs4 import BeautifulSoup
import time
from urllib.parse import quote
import pandas as pd
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCROLL_PAUSE_TIME = 2

#제목/본문/작성자/작성일/본문링크
#"의류관리기", "스타일러", "에어 드레서", "의류청정기"
cnt = 0
driver = webdriver.Chrome()
driver.implicitly_wait(3)
query = "의류관리기"
year_query=["from20110501to20111231"
            ,"from20120101to20121231"
            ,"from20130101to20131231"
            ,"from20140101to20141231"
            ,"from20150101to20151231"
            ,"from20160101to20161231"
            ,"from20170101to20171231"
            ,"from20180101to20181231"
            ,"from20190101to20191231"
            ,"from20200101to20201231"
            ,"from20210101to20211231"
            ,"from20220101to20221231"
            ,"from20230101to20230531"
            ]
f = open('result_naver2.txt', 'w')
df = pd.DataFrame()

# DataFrame을 Excel 파일로 저장합니다.
df.to_excel("output_naver.xlsx")


def text_parse(obj):
    if obj is not None:
        obj = obj.get_text()
    else:
        obj = "Not found"
    return obj

def href_parse(obj):
    if obj is not None:
        obj = obj['href']
    else:
        obj = "Not found"
    return obj

def delete_iframe(url):
    headers = {
    "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status() # 상태 코드가 200 OK가 아니면   예외를 발생
    except (requests.HTTPError, requests.ConnectionError, requests.exceptions.SSLError):
        print(f"{url} is not accessible. Skipping...")
        return "Not Accessible"
    soup = BeautifulSoup(response.text, 'html.parser')
    if soup.iframe is None: 
        print(f"No iframe found in {url}. Skipping...")
        return "Not Accessible"
    src_url = "https://blog.naver.com/" + soup.iframe["src"]
    return src_url


def text_scrap(url, check):
    headers = {
    "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X10_15_7) AppleWebKit/537.36 (KHTML,like Gecko) Chrome/91.0.4472.101 Safari/537.36",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status() # 상태 코드가 200 OK가 아니면   예외를 발생
    except (requests.HTTPError, requests.ConnectionError, requests.exceptions.SSLError):
        print(f"{url} is not accessible. Skipping...")
        return "Not Accessible"
    soup = BeautifulSoup(response.text, 'html.parser')
    if not check:
        text = soup.find("div", class_='se-main-container')
        if text is not None:
            text = text.get_text()
        else:
            text = "Not Found"
    else:
        text = soup.find('div', {'id': 'postListBody'})
        if text is not None:
            text = text.get_text(strip=True)
        else:
            text = "Not Found"
    return text

def remove_illegal_chars(val):
    if isinstance(val, str):
        # XML 1.0 legal chars
        val = re.sub(u'[\x00-\x08\x0B-\x0C\x0E-\x1F\uD800-\uDFFF\uFFFE\uFFFF]', '', val)
    return val

df = pd.DataFrame(columns=['작성자', '제목', '링크', '작성일', '본문'])

for i in range(0,13):
    print("i : ",i)
    f.write("<<<<<<<20"+str(i + 11)+">>>>>>>\n")
    url = "https://search.naver.com/search.naver?where=blog&query=" + quote(query) + "&sm=tab_opt&nso=so%3Ar%2Cp%3A" + quote(year_query[i]) + "%2Ca%3Aall"
    driver.get(url)
    print(year_query[i])
    headers = {
    "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.   4472.101 Safari/537.36",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    actions = ActionChains(driver)
    for _ in range(600):  # 2000번 스크롤
        actions.send_keys(Keys.PAGE_DOWN)  # 페이지 다운 키를 보냄
        actions.perform()  # 동작 실행
        time.sleep(0.1)  # 로딩 대기

    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Wait to load page
    time.sleep(SCROLL_PAUSE_TIME)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    posts = soup.find_all("div", class_="view_wrap")
    for post in posts:
        cnt = cnt +1
        user_name = text_parse(post.find("a",class_="name") )   
        f.write("작성자 : "+ user_name + "\n")
        post_title = text_parse(post.find('div',class_='title_area'))
        f.write("제목 : "+ post_title + "\n")
        print(post_title)
        post_url = href_parse(post.find("a",class_='title_link'))
        f.write("링크 : "+ post_url + "\n")
        post_date = text_parse(post.find("span",class_='sub'))
        f.write("작성일 : " + post_date + "\n")
        print(cnt, post_date)
        #본문
        post_iframe = delete_iframe(post_url)
        if post_iframe == "Not Accessible":
            continue
        post_main = text_scrap(post_iframe, i<8).replace("\n", "\t");
        if post_main == "Not Accessible":
            continue
        f.write("본문 : " + post_main + "\n")
        new_row = pd.DataFrame([{'작성자': user_name, '제목': post_title, '링크': post_url, '작성일': post_date, '본문': remove_illegal_chars(post_main)}])
        df = pd.concat([df, new_row],ignore_index=True)
        f.write("-"*50 + "\n")   

df.to_excel('output_naver.xlsx',index=False)





print(cnt)