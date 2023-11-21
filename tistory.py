import requests
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import pandas as pd

from urllib.parse import quote
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

df = pd.DataFrame(columns=['작성자', '제목', '링크', '작성일', '본문'])


#제목/본문/작성자/작성일/본문링크
#"의류관리기", "스타일러", "에어 드레서", "의류청정기"
cnt = 0
driver = webdriver.Chrome()
driver.implicitly_wait(3)
query = "의류관리기"

f = open('result_tistory.txt', 'w')

url = "https://www.tistory.com/m/search?query=" +quote(query)+"&tab=post"
driver.get(url)
headers = {
"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.   4472.101 Safari/537.36",
"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}
response = requests.get(url, headers=headers, verify=False)
response.raise_for_status()
soup = BeautifulSoup(response.text, 'html.parser')
SCROLL_PAUSE_TIME = 3
# Get scroll height
actions = ActionChains(driver)

for _ in range(300):  # 2000번 스크롤
    actions.send_keys(Keys.PAGE_DOWN)  # 페이지 다운 키를 보냄
    actions.perform()  # 동작 실행
    time.sleep(0.1)  # 로딩 대기


last_height = driver.execute_script("return document.body.scrollHeight")
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
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    if soup.iframe is None: 
        print(f"No iframe found in {url}. Skipping...")
        return "Not Accessible"
    src_url = "https://blog.naver.com/" + soup.iframe["src"]
    return src_url
def text_scrap(url):
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
    return soup

def remove_illegal_chars(val):
    if isinstance(val, str):
        # XML 1.0 legal chars
        val = re.sub(u'[\x00-\x08\x0B-\x0C\x0E-\x1F\uD800-\uDFFF\uFFFE\uFFFF]', '', val)
    return val

for j in range(0,2000):
    # Scroll down to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # Wait to load page
    time.sleep(SCROLL_PAUSE_TIME)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    posts = soup.find_all("li")
    for post in posts:
        cnt = cnt +1
        post_title = text_parse(post.find('strong',class_='tit_blog'))
        f.write("제목 : "+ post_title + "\n")
        print(post_title)
        
        post_url = href_parse(post.find("a"))
        f.write("링크 : "+ post_url + "\n")
        print(post_url)
        post_date = text_parse(post.find("span",class_='txt_date'))
        f.write("작성일 : " + post_date + "\n")
        print(post_date)
        #본문
        post_main = text_scrap(post_url)
        if post_main == "Not Accessible":
            print(f"{post_url} is not accessible. Skipping...")
            continue
        user_name = text_parse(post_main.find("cite",class_="by_blog") )   
        f.write("작성자 : "+ user_name + "\n")
        print(user_name)
        post_main_texts = post_main.find_all("p")
        texts = []
        f.write("본문 : ")
        for post_main_text in post_main_texts:
            f.write(post_main_text.get_text() + "\n")
            texts.append(post_main_text.get_text())
            print(post_main_text)
        f.write("-"*50 + "\n")
        post_main_all_text = "\n".join(texts)

        new_row = pd.DataFrame([{'작성자': user_name, '제목': post_title, '링크': post_url, '작성일': post_date, '본문': remove_illegal_chars(post_main_all_text)}])
        df = pd.concat([df, new_row],ignore_index=True)
    # Calculate new scroll height and compare with last     scroll height
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height



df.to_excel("output_tistory.xlsx", index=False)

print(cnt)