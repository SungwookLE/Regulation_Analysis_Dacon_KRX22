# 크롤링시 필요한 라이브러리 불러오기
# -*- coding: UTF-8 -*-
from bs4 import BeautifulSoup
import requests
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

class NaverNEWSCrawler:

    def __init__(self, keyword, start_pg=1, end_pg=1):
        # 웹드라이버 설정
        #Colab에선 웹브라우저 창이 뜨지 않으므로 별도 설정한다.
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')        # Head-less 설정
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome('chromedriver', options=options)

        # 검색어 입력
        self.search= keyword
        self.start_pg = start_pg
        self.end_pg = end_pg
        # naver url 생성
        self.search_urls = NaverNEWSCrawler.makeUrl(self.search, self.start_pg, self.end_pg)


        ## selenium으로 navernews만 뽑아오기##
        driver.implicitly_wait(3)
        # selenium으로 검색 페이지 불러오기 #
        naver_urls = []
        for search_url in self.search_urls:
            driver.get(search_url)
            time.sleep(1)  # 대기시간 변경 가능

            # 네이버 기사 눌러서 제목 및 본문 가져오기#
            # 네이버 기사가 있는 기사 css selector 모아오기
            search_news = driver.find_elements(By.CSS_SELECTOR, 'a.info')

            # 위에서 생성한 css selector list 하나씩 클릭하여 본문 url얻기
            for search_new in search_news:
                search_new.click()

                # 현재탭에 접근
                driver.switch_to.window(driver.window_handles[1])
                time.sleep(3)  # 대기시간 변경 가능

                # 네이버 뉴스 url만 가져오기
                url = driver.current_url

                if "news.naver.com" in url:
                    naver_urls.append(url)
                    print(url)
                else:
                    pass
                
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            
        ###naver 기사 본문 및 제목 가져오기###
        # ConnectionError방지
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/98.0.4758.102"}

        titles = []
        contents = []
        news_dates = []

        for naver_url in naver_urls:
            original_html = requests.get(naver_url, headers=headers)
            html = BeautifulSoup(original_html.text, "html.parser")
            # 뉴스 제목 가져오기
            title = html.select("div#ct > div.media_end_head.go_trans > div.media_end_head_title > h2")
            # list합치기
            title = ''.join(str(title))
            # html태그제거
            pattern1 = '<[^>]*>'
            title = re.sub(pattern=pattern1, repl='', string=title)
            titles.append(title)

            # 뉴스 본문 가져오기
            content = html.select("div#dic_area")

            # 기사 텍스트만 가져오기
            # list합치기
            content = ''.join(str(content))
            # html태그제거 및 텍스트 다듬기
            content = re.sub(pattern=pattern1, repl='', string=content)
            pattern2 = """[\n\n\n\n\n// flash 오류를 우회하기 위한 함수 추가\nfunction _flash_removeCallback() {}"""
            content = content.replace(pattern2, '')
            contents.append(content)
                    
            # 날짜 가져오기
            html_date = html.select_one("div#ct> div.media_end_head.go_trans > div.media_end_head_info.nv_notrans > div.media_end_head_info_datestamp > div > span")
            if html_date != None:
                news_date = html_date.attrs['data-date-time']
                news_dates.append(news_date)
            else : 
                news_dates.append("None")
        driver.quit()
        # 데이터프레임으로 정리(titles,url,contents)

        self.news_df = pd.DataFrame({'date' : news_dates,
                        'title': titles, 
                        'content': contents,
                        'link': naver_urls, 
                        })

        self.news_df.to_csv('file/NaverNews_%s.csv' % self.search, index=False, encoding='utf-8-sig')
        return

    # 크롤링할 url 생성하는 함수 만들기(검색어, 크롤링 시작 페이지, 크롤링 종료 페이지)
    def makeUrl(search, start_pg, end_pg):
        if start_pg == end_pg:
            start_page = start_pg
            url = "https://search.naver.com/search.naver?where=news&sm=tab_pge&query=" + search + "&start=" + str(start_page)
            return [url]

        else:
            urls = []
            for i in range(start_pg, end_pg + 1):
                page = i
                url = "https://search.naver.com/search.naver?where=news&sm=tab_pge&query=" + search + "&start=" + str(page)
                urls.append(url)
            return urls
    

if __name__ == "__main__":
    nnews =NaverNEWSCrawler(keyword=r"윤석열")
    print(nnews.news_df)