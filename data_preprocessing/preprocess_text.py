import re
import unicodedata
from konlpy.tag import Hannanum
from pynori.korean_analyzer import KoreanAnalyzer
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd

class TextCleaner:
    def remove_unicode(input_str):
        # 유니코드 :  https://gist.github.com/Pusnow/aa865fa21f9557fa58d691a8b79f8a6d
        try:
            input_str = str(input_str)
            
        except (TypeError, NameError): # unicode is a default on python 3 
             pass

        text = unicodedata.normalize('NFKC', input_str).encode('utf-8','ignore').decode("utf-8")
            
        return text

    def clean_ko_sentences(sentences):
        sentence = TextCleaner.remove_unicode(sentences)
        # 정규 표현식 필터
        RE_FILTER = re.compile(r"[#▲,<>!?\"'·:;=~()]") # [] 안에 제거할 정규표현식을 추가한다
        # 특수기호 제거
        sentences = re.sub(RE_FILTER, "", sentence)
        sentences = re.sub(r"[^A-Za-z0-9가-힣?!,.¿]+", " ",sentences) 
        sentences = re.sub(r"\s"," ", sentences)# \n도 공백으로 대체해줌
        sentences = sentences.strip()  
        
        return str(sentences)
    
    def clean_ko_nouns(nounsList):
        nouns_list = []

        for noun in nounsList:
            if len(noun) > 1: # 한 글자 이하일때 삭제
                p = re.compile(r"[^0-9]+") # 숫자로 시작되는 글자 삭제
                noun = p.match(noun)
                if noun:
                    nouns_list.append(noun.group())
        
        return nouns_list

    def html_delete(raw_review):
        # HTML 코드 제거
        clean_text = BeautifulSoup(raw_review, "html.parser").get_text()
        return clean_text

class NounExtracter:

    def Morph_ko_document(sentence_List, database = "hannanum"):
        # KoNLPy 형태소분석기 설정 '
        # 형태소 분석기 적용부분 
        nouns = []

        if database == "hannanum":
            analyzer = Hannanum()
            for sentence in sentence_List:
                sentence = TextCleaner.clean_ko_sentences(sentence)
                nouns_list = analyzer.nouns(str(sentence))
                nouns_list=TextCleaner.clean_ko_nouns(nouns_list)
                nouns.append(nouns_list)

        elif database == "nori":
            analyzer = KoreanAnalyzer(
              decompound_mode='DISCARD', # DISCARD or MIXED or NONE
              infl_decompound_mode='DISCARD', # DISCARD or MIXED or NONE
              discard_punctuation=True,
              output_unknown_unigrams=False,
              pos_filter=False, stop_tags=['JKS', 'JKB', 'VV', 'EF'],
              synonym_filter=False, mode_synonym='NORM', # NORM or EXTENSION
            ) 
            for sentence in sentence_List:
                sentence = TextCleaner.clean_ko_sentences(sentence)
                # print(sentence)
                nouns_list = analyzer.do_analysis(str(sentence))['termAtt']
                nouns_list=TextCleaner.clean_ko_nouns(nouns_list)
                nouns.append(nouns_list)

        return nouns 

if __name__ == "__main__":
    txt = TextCleaner.clean_ko_sentences("asdzxc@뷁ㄹ뷂눎ㄴㅇㅂㅈㄷ____ㄴㅁㅋㅌ취차 줘")
    print(txt)

    sentence_list = ["나는 정말 즐거운 인생을 살고 싶고, 또 부자가 되고싶다!", "동해물과 백두산이 마르고 닳도록, 하느님이 보우하사 우리나라 만세~~!"]
    nouns = NounExtracter.Morph_ko_document(sentence_list, database = "hannanum")
    print(nouns)