import enum
import olefile
import pandas as pd
import os
import zlib
import struct
import re

class FinanaceRegulation_HWP_Parser:
    def __init__(self, fname, directory):
        self.root = os.path.join(directory, fname)
        self.fname = fname

        f = olefile.OleFileIO(self.root)
        dirs = f.listdir()
        # HWP 파일 검증
        if ["FileHeader"] not in dirs or \
            ["\x05HwpSummaryInformation"] not in dirs:
            raise Exception("Not Valid HWP.")
        
        # 문서 포맷 압축 여부 확인
        header = f.openstream("FileHeader")
        header_data = header.read()
        is_compressed = (header_data[36] & 1) == 1

        # Body Sections 불러오기
        nums = []
        for d in dirs:
            if d[0] == "BodyText":
                nums.append(int(d[1][len("Section"):]))
        sections = ["BodyText/Section"+str(x) for x in sorted(nums)]

        # 전체 text 추출
        text = ""
        for seciton in sections:
            bodytext = f.openstream(seciton)
            data = bodytext.read()
            if is_compressed:
                unpacked_data = zlib.decompress(data,-15)
            else:
                unpacked_data = data
        
            # 각 Section 내 text 추출
            section_text = ""
            i = 0
            size = len(unpacked_data)
            while i < size:
                header = struct.unpack_from("<I", unpacked_data, i)[0]
                rec_type = header & 0x3ff
                rec_len = (header >> 20) & 0xfff

                if rec_type in [67]:
                    rec_data = unpacked_data[i+4:i+4+rec_len]
                    section_text += rec_data.decode('utf-16')
                    section_text += "\n"

                i += 4 + rec_len

            text += section_text
            text += "\n"

        self.raw_text = text

    def parse_from_text(self):

        text_line_token =re.sub(r"[^a-zA-Z0-9가-힣.\-\r\n\s]", '', self.raw_text)
        for idx, line in enumerate(text_line_token.splitlines()):
            match_result = re.match("\d{1,2}", line)
            if match_result:
                if (line == "1.규제사무명"):
                    start_idx1 = idx
                elif (line == "2.규제조문"):
                    start_idx2 = idx
                elif (line == "3.위임법령"):
                    start_idx3 = idx
                elif (line == "4.유형"):
                    start_idx4 = idx
                elif (line == "5.입법예고"):
                    start_idx5 = idx
                elif (line == "6.추진배경"):
                    start_idx6 = idx
                elif (line == "7.규제내용"):
                    start_idx7 = idx
                elif (line == "8.피규제집단      및"):
                    start_idx8 = idx
                elif (line == "9.도입목표 및" or line =="9.규제목표"):
                    start_idx9 = idx
                elif (line == "10.비용편익분석" or line == "10.영향평가 여부"):
                    start_idx10 = idx
                elif (line == "11.영향평가 여부" or line == "11. 비용편익"):
                    start_idx11 = idx

        contents_dict = dict()
        try: 
            contents_dict["1.규제사무명"] =  ' '.join((text_line_token.splitlines())[start_idx1+1:start_idx2])  
            contents_dict["2.규제조문"] =  ' '.join((text_line_token.splitlines())[start_idx2+1:start_idx3])
            contents_dict["3.위임법령"] =  ' '.join((text_line_token.splitlines())[start_idx3+1:start_idx4])
            contents_dict["4.유형"] =  ' '.join((text_line_token.splitlines())[start_idx4+1:start_idx5])
            contents_dict["5.입법예고"] =  ' '.join((text_line_token.splitlines())[start_idx5+1:start_idx6])
            contents_dict["6.추진배경및정부개입필요성"] =  ' '.join((text_line_token.splitlines())[start_idx6+2:start_idx7])
            contents_dict["7.규제내용"] =  ' '.join((text_line_token.splitlines())[start_idx7+1:start_idx8])
            contents_dict["8.피규제집단및이해관계자"] =  ' '.join((text_line_token.splitlines())[start_idx8+2:start_idx9])
            contents_dict["9.도입목표및기대효과"] =  ' '.join((text_line_token.splitlines())[start_idx9+2:start_idx10])
            contents_dict["10.비용편익분석"] =  ' '.join((text_line_token.splitlines())[start_idx10+1:start_idx11])  
        except Exception as e: 
            print(f"\n[예외처리]: {self.fname} 파일의 서식이 예상과 다릅니다. {e}")

        return contents_dict
                

if __name__ == "__main__":
    fsc = FinanaceRegulation_HWP_Parser("3.외부감사규정규제영향분석서.hwp", "file")

    res = fsc.parse_from_text()
    print(res)