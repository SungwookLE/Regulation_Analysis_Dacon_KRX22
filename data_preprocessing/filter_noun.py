from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import pandas as pd
from data_preprocessing.preprocess_text import NounExtracter

'''
# data_preprocessing.filter_noun.py
'''

from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import pandas as pd
# from data_preprocessing.preprocess_text import NounExtracter

class NounsFilter_Regulation:
    def __init__(self, input_corpus):
        self.input_corpus = input_corpus.dropna() # one sentence

        self.get_frequency()
        self.get_tfidf()

    def get_frequency(nouns): 
        counter = dict()

        for noun in nouns:
            if noun in counter.keys():
                counter[noun] += 1
            else:
                counter[noun] =1

        counter_dict = pd.DataFrame(counter.items(), columns=["word", "freq"])
        counter_dict = counter_dict.sort_values(["freq"], ascending=[False]) 

        return counter_dict
    
    def get_tfidf(self):
        self.vectorizer = TfidfVectorizer()
        self.tfidf_value = self.vectorizer.fit_transform(self.input_corpus)

        self.make_tfidf_dict()
        self.get_NoMeaningRate()
        self.get_tfidf_feature_names()

        return self.tfidf_value 


    def make_tfidf_dict(self):
        word = self.vectorizer.inverse_transform(self.tfidf_value)
        value = (self.tfidf_value).data

        self.tfidf_dict = pd.DataFrame(data=value).transpose()
        self.tfidf_dict.index = ["value"]
        self.tfidf_dict.columns = word[0]

        return self.tfidf_dict


    def Tfidf(regulation_words):
        tv = TfidfVectorizer()
        W = 0.15 

        word=[]
        for i in regulation_words:
            word.append(str(i))

        tv_result = tv.fit_transform(word)
        a = (tv_result.data> W )*1
        tv_result.data = a

        word_num =[]
        word_value = []

        for i, (b, e) in enumerate(zip(tv_result.indptr, tv_result.indptr[1:])):
            for idx in range(b, e):
                j = tv_result.indices[idx]
                d = tv_result.data[idx]
                word_num.append(j)
                word_value.append(d)

        result = pd.DataFrame({"word_num" : word_num})
        result["value"] = word_value
        tfidf_values = result.groupby("word_num").sum()

        word = tv.get_feature_names()
        tfidf_values["word"] = word
        tfidf_values.index = tfidf_values["word"]
        del tfidf_values["word"]

        return tfidf_values

    def tfidf_result(nomarl_freq, tfidf_values ):
      result = pd.merge(nomarl_freq, tfidf_values, on="word", how='left')
      result["NMR"] = (result["freq"]-result["value"])/result["freq"] #NMR = NoMeaningRate
      result = result.sort_values(["freq"], ascending=[False])
      return result 

    def get_tfidf_feature_names(self):
        self.tfidf_unique_word = self.vectorizer.get_feature_names() # 유니크한 단어 목록
        return self.tfidf_unique_word

    def get_NoMeaningRate(self):
        NMR = (self.counter_dict.loc["freq"] - self.tfidf_dict.loc["value"]) / self.counter_dict.loc["freq"]  #NMR = NoMeaningRate
        NMR.dropna(inplace=True)
        NMR=NMR.sort_values(ascending=True)

        self.NMR = NMR
        return self.NMR 

    def pick_the_best_K_nouns(self, K):
        return self.NMR.head(K).index


class NounsFilter_News:
    def __init__(self, input_corpus=None):
        self.input_corpus = input_corpus
        if input_corpus is not None:
            self.input_corpus = input_corpus.dropna() # one sentence

        self.get_frequency()
        self.get_tfidf()

    def get_frequency(self):
        self.nouns = NounExtracter.Morph_ko_document(self.input_corpus, database = "hannanum")

        counter = dict()
        for nouns in self.nouns:
            for noun in nouns:
                if noun in counter.keys():
                    counter[noun] += 1
                else:
                    counter[noun] =1

        self.counter_dict = pd.DataFrame(counter, index=["freq"])
        return self.counter_dict
    
    def get_tfidf(self):
        self.vectorizer = TfidfVectorizer()
        self.tfidf_value = self.vectorizer.fit_transform(self.input_corpus)

        self.make_tfidf_dict()
        self.get_NoMeaningRate()
        self.get_tfidf_feature_names()

        return self.tfidf_value 


    def make_tfidf_dict(self):
        word = self.vectorizer.inverse_transform(self.tfidf_value)
        value = (self.tfidf_value).data

        self.tfidf_dict = pd.DataFrame(data=value).transpose()
        self.tfidf_dict.index = ["value"]
        self.tfidf_dict.columns = word[0]

        return self.tfidf_dict

    def get_tfidf_feature_names(self):
        self.tfidf_unique_word = self.vectorizer.get_feature_names() # 유니크한 단어 목록
        return self.tfidf_unique_word

    def get_NoMeaningRate(self):
        NMR = (self.counter_dict.loc["freq"] - self.tfidf_dict.loc["value"]) / self.counter_dict.loc["freq"]  #NMR = NoMeaningRate
        NMR.dropna(inplace=True)
        NMR=NMR.sort_values(ascending=True)

        self.NMR = NMR
        return self.NMR 

    def pick_the_best_K_nouns(self, K):
        return self.NMR.head(K).index


if __name__=="__main__":

    input = pd.Series(['단위백만원 비용 편익 순비용 피규제자 피규제자 이외 정성분석 조달금리 하락시\
        금융회사의 인센티브 축소 조달금리를 반영하는 민간중금리 금리요건 합리화로 중금리대출 활성화\
        주요내용  조달금리 상승시에는 민간중금리 대출 금리상한이 상승함에 따라 금융회사에게는 인센티브가 확대되고\
        고금리로 대출받던 중저신용자에게는 보다 낮은 금리로 대출을 받을 수 있는 기회가 증가  조달금리 하락시에는 민간중금리 대출\
        금리상한이 하락함에 따라 금융회사의 인센티브는 축소되나 이는 조달비용 하락에 따른 효과로서 금융회사에게 실질적 부담이 발생한다고 보기 어려운 측면이 있으며.\
        중저신용자는 낮은 금리로 중금리대출 활용 가능 민간중금리 기준에 조달금리 변경을 반영함으로써 금융회사와 중저신용자에 대한 순편익 증대'])

    filter = NounsFilter_News(input)
    print(filter.pick_the_best_K_nouns(10))