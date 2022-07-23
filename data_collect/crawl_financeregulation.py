import os
import re
from urllib import request
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import requests
import pandas as pd
from data_collect.parse_HWPfile import FinanaceRegulation_HWP_Parser

class FinanceRegulationCrawler:
    '''
    return dict specification: (딕셔너리 구조(칼럼) 명세서)
        1. subject: [o] 상세 페이지 제목
        2. date: [o] 상세 페이지 작성일
        3. category1: [o] 대분류
        4. category2: [o] 중분류
        5. category3: [o] 예고일정
        6. contents: [x] 상세 페이지 contents (string text type, parsing 안되어있음, 주석처리 해둠)
        7. fname: [o] 상세페이지의 첨부파일 이름
        8. download_url: [o] 첨부파일 다운로드 링크
        9. attached_contents: [o] 첨부 파일의 contents (dict type, parsing 되어있음)
            9-1. 1.규제사무명
            9-2. 2.규제조문
            9-3. 3.위임법령
            9-4. 4.유형
            9-5. 5.입법예고
            9-6. 6.추진배경및정부개입필요성
            9-7. 7.규제내용
            9-8. 8.피규제집단및이해관계자
            9-9. 9.도입목표및기대효과
            9-10. 10.비용편익분석
    '''
    def __init__(self):
        self.site = "https://www.fsc.go.kr"
        self.download_tag = "/comm/getFile?"
        self.detail_tag = "/view?noticeId"

    def crawl_page(self, folder):
        self.folder = folder

        #999페이지까지 크롤링하여도 되나, 데모코드에서는 2페이지까지만 크롤링
        #max_page_num = 999 
        max_page_num = 2
        
        for page_num in range(1,max_page_num):
            page_param = f"/po040301?curPage={page_num}"
            # request 모듈을 사용하여 웹 페이지의 내용을 가져온다.
            url = self.site + page_param
            print(f"크롤링 진행 중 ... :{url}")
            r = requests.get(url)

            # beautiful soup 초기화
            soup = BeautifulSoup(r.text, "html.parser")
            items = soup.find_all("a")
            res = self.parse_the_page(items)

            if len(res) <= 0:
                print(f"실패: 페이지{page_num} 비어있음")
                break
            else:
                print(f"완료: 페이지{page_num}")
            
            yield res

    def download_attached_file(self, url, fname, directory):
        try:
            root = os.path.join(directory, fname)
            request.urlretrieve(url, root)

        except HTTPError as e:
            print(f"첨부파일 다운로드 실패, {url, fname}")
            return

    def parse_the_page(self, items):

        page_dict = dict()
        for item_idx, item in enumerate(items):
            if self.detail_tag in item.get("href"):
                item_dict = dict()
                detail_url = self.site + item.get('href')[1:]
                item_dict["detail_url"] = detail_url

                detail_r = requests.get(detail_url)
                detail_soup = BeautifulSoup(detail_r.text, "html.parser")

                subject =  detail_soup.select_one(".board-view-wrap > .header > .subject").get_text()
                day = detail_soup.select_one(".board-view-wrap > .header > .day").get_text().strip().split('\n')
                info = detail_soup.select_one(".board-view-wrap > .header > .info").get_text().strip().split('\n')
                contents = detail_soup.select_one(".board-view-wrap > .body > .cont").get_text().strip()
                
                item_dict["subject"] = subject
                item_dict["date"] = day[0]
                item_dict["cagegory1"] = info[0]
                item_dict["cagegory2"] = info[1]
                item_dict["cagegory3"] = info[2]
                #item_dict["contents"] = re.sub(r"[^a-zA-Z0-9가-힣.,\s\n]", "", contents)

                download_names = detail_soup.select(".body > .file > .file-list-wrap > .file-list > .name")
                download_urls  = detail_soup.select(".body > .file > .file-list-wrap > .file-list > .ico + .download")

                item_dict["fname"] = list()
                item_dict["download_url"] = list()
                item_dict["attached_contents"] = list()
                
                for item in zip(download_names, download_urls):
                    name = item[0].get_text().strip()
                    name = re.sub(r"[^a-zA-Z0-9가-힣._]", ' ', name).split()[:-2]
                    fname = ''.join(name)
                    if self.download_tag in item[1].find(href=True)['href']: #첨부파일 다운로드 링크가 있는 것들 중,
                        if re.search(r"hwp$", fname, re.IGNORECASE): #한글문서 첨부파일인 것들과
                            if re.search(r"규제영향분석서.hwp$", fname): #한글 파일의 이름에 '규제영향분석서'라는 문구가 있는 경우
                                download_url = self.site + item[1].find(href=True)['href']
                                self.download_attached_file(download_url, fname, self.folder)
                                item_dict["fname"].append(fname)
                                item_dict["download_url"].append(download_url)
                                hwp_handler = FinanaceRegulation_HWP_Parser(fname, self.folder)
                                hwp_res = hwp_handler.parse_from_text()
                                item_dict["attached_contents"].append(hwp_res)

                page_dict[item_idx] = item_dict

        return page_dict

if __name__ == "__main__":
    fsc = FinanceRegulationCrawler()
    res = fsc.crawl_page(folder="file")
    for r in res:
        print(f"\n\n{r}\n\n")
