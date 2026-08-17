#!/usr/bin/env python3
"""Apply Vietnamese translations to pending menu.json and bio.json entries."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MENU_TRANSLATIONS: dict[str, tuple[str, str]] = {
    "丹氾": ("[loi extract]", "UNK"),
    "于瓊": ("Vu Quynh", "V.Quy"),
    "仲子": ("Vien Dam", "V.Dam"),
    "仲康": ("Dien Vi", "D.Vi"),
    "仲權": ("Ha Hau Ba", "H.Ba"),
    "仲異": ("Ton Quyen", "T.Quy"),
    "仲直": ("Phap Chinh", "P.Chi"),
    "仲翔": ("Han Toai", "H.Toa"),
    "休元": ("Hoang Quyen", "H.Quy"),
    "伯仁": ("Chau Thu", "C.Thu"),
    "伯恭": ("Truong Dich", "T.Di"),
    "伯業": ("Cong Ton Toan", "C.Toan"),
    "伯符": ("Ton Sach", "T.Sac"),
    "伯約": ("Tuong Vi", "T.Vi"),
    "伯緒": ("Luong Ky", "L.Ky"),
    "伯言": ("Lu Ton", "L.Ton"),
    "佐資": ("[loi extract]", "UNK"),
    "何燒戈": ("[loi extract]", "UNK"),
    "侯乾": ("Hau Can", "H.Can"),
    "元仲": ("Tao Due", "T.Du"),
    "元儉": ("Lieu Hoa", "L.Ho"),
    "元凱": ("Luc Tich", "L.Tic"),
    "元則": ("Hoan Pham", "H.Pha"),
    "元圖": ("Quach Do", "G.Do"),
    "元宗": ("Ton Hao", "T.Hao"),
    "元恩": ("Vuong Lang", "W.Lang"),
    "元明": ("Quan Khac", "G.Kha"),
    "元皓": ("Dien Phong", "D.Pho"),
    "元穎": ("Luu Phuc", "L.Ph"),
    "元紹": ("[loi extract]", "UNK"),
    "元讓": ("Ha Hau Don", "H.Don"),
    "公仁": ("Tuong Quan", "T.Qua"),
    "公嗣": ("Luu Thien", "L.Thi"),
    "公壽": ("Luu Vinh", "L.Vi"),
    "公悌": ("Phuc Tan", "P.Ta"),
    "公禮": ("Ton Thieu", "T.Thi"),
    "公紀": ("Lu Tong", "L.To"),
    "公臺": ("Tran Cong", "T.Co"),
    "公舉": ("Than Dam", "T.Da"),
    "公覆": ("Hoang Gai", "H.Gai"),
    "公路": ("Vien Thu", "V.Thu"),
    "公達": ("Tu Ma Y", "T.M.Y"),
    "初延": ("[loi extract]", "UNK"),
    "勒萌": ("Vuong Ky", "W.Ky"),
    "升鋒": ("Tang Tung", "T.Tu"),
    "友若": ("Hua Chu", "H.Chu"),
    "叔嗣": ("Truong Huu", "T.Huu"),
    "叔弼": ("Ton Khang", "T.Kha"),
    "叔明": ("Ton Kiet", "T.Kie"),
    "叔穎": ("Dong Uy", "D.Uy"),
    "壽成": ("Tieu Thua", "T.Th"),
    "奉先": ("Lu Bo", "Lu Bo"),
    "奕晃": ("[loi extract]", "UNK"),
    "妙才": ("Ha Hau Uyen", "H.Uye"),
    "威公": ("Dong Uy", "D.Uy"),
    "威彥": ("Tran Uong", "T.Uo"),
    "子丹": ("Tao Chan", "T.Cha"),
    "子建": ("Tao Chi", "T.Chi"),
    "子恪": ("Gia Cat Khac", "G.CKh"),
    "子柔": ("Khoai Luong", "K.Lu"),
    "子桓": ("Tao Phi", "T.Phi"),
    "子臺": ("[loi extract]", "UNK"),
    "子遠": ("Tu Vien", "T.Vien"),
    "子陽": ("Duong Nghi", "D.Ng"),
    "子龍": ("Trieu Van", "T.Van"),
    "孔休": ("Khong Huu", "K.Huu"),
    "孕羆": ("[loi extract]", "UNK"),
    "孝士仁": ("Tang Hoi", "T.Hoi"),
    "孝銀": ("[loi extract]", "UNK"),
    "孟卓": ("Truong Mieu", "T.Mi"),
    "季常": ("Ma Tu", "Ma Su"),
    "季弼": ("Tran Co", "T.Co"),
    "季文": ("Ky Van", "Ky Van"),
    "季玉": ("Luu Ky", "L.Ky"),
    "季珪": ("Thoi Diem", "T.Di"),
    "季行": ("Canh Ky", "C.Ky"),
    "安民": ("Quan Binh", "Q.Bi"),
    "宣高": ("Lu Khang", "L.Kha"),
    "寧曄": ("Mau Thach", "M.Tha"),
    "山善": ("[loi extract]", "UNK"),
    "帶來洞主": ("Mang Lai dong chu", "MLDong"),
    "平叔": ("Ha Uyen", "H.Uye"),
    "幼平": ("Chu Thai", "C.Thai"),
    "幼節": ("Tran Dang", "T.Da"),
    "幼臺": ("Ton Tinh", "T.Ti"),
    "康孔才": ("Khong Dung", "K.Dun"),
    "彭祖": ("Tao Vu", "T.Vu"),
    "德信": ("Vuong Binh", "W.Bin"),
    "德偉": ("Phi Y", "Phi Y"),
    "德奕": ("[loi extract]", "UNK"),
    "德容": ("Truong Ky", "T.Ky"),
    "德彰": ("Tao Chuong", "T.Chu"),
    "德樞": ("Trinh Dong", "T.Do"),
    "德瑜": ("Chu Du", "Chu Du"),
    "德祖": ("Duong Tu", "D.Tu"),
    "德節": ("Truong Hoa", "T.Ho"),
    "德謀": ("Thanh Pho", "T.Pho"),
    "德豔": ("Tong Du", "T.Du"),
    "德達": ("Nham Kien", "N.Kie"),
    "恪優": ("[loi extract]", "UNK"),
    "恪堪": ("[loi extract]", "UNK"),
    "恪邢": ("[loi extract]", "UNK"),
    "恭祖": ("Dau Khiem", "D.Kh"),
    "悄鄏": ("[loi extract]", "UNK"),
    "惠恕": ("Truong On", "T.On"),
    "憟藇": ("[loi extract]", "UNK"),
    "承明": ("Luu Ba", "L.Ba"),
    "撠亂": ("[loi extract]", "UNK"),
    "攸之": ("Tuong Uy", "T.Uy"),
    "敬仲": ("Truong Cung", "T.Cu"),
    "文博": ("[loi extract]", "UNK"),
    "文嚮": ("[loi extract]", "UNK"),
    "文性": ("[loi extract]", "UNK"),
    "文烈": ("Tao Tu", "T.Tu"),
    "文然": ("Cat Mieu", "C.Mieu"),
    "文珪": ("Tran Ung", "T.Ung"),
    "文翼": ("Truong Ho", "T.Ho"),
    "文若": ("Tun Tu", "Tun Tu"),
    "文遠": ("Truong Lieu", "T.Lie"),
    "明傕": ("Ly Que", "L.Que"),
    "明韋": ("Dien Vi", "D.Vi"),
    "暀撟": ("[loi extract]", "UNK"),
    "暀萵": ("[loi extract]", "UNK"),
    "暀蔚": ("[loi extract]", "UNK"),
    "本初": ("Vien Thieu", "V.Thi"),
    "朵思大王": ("Do Tu Dai Vuong", "DoTuDV"),
    "桓衛": ("[loi extract]", "UNK"),
    "桓觸": ("[loi extract]", "UNK"),
    "棓鉾": ("[loi extract]", "UNK"),
    "椪鼮": ("[loi extract]", "UNK"),
    "榮譚": ("Vien Dam", "V.Dam"),
    "權皓": ("[loi extract]", "UNK"),
    "武叔": ("Vo Ban", "V.Ban"),
    "永先": ("Truong Tong", "T.To"),
    "沙摩可": ("Sa Ma Kha", "SaMaKha"),
    "滬躑": ("[loi extract]", "UNK"),
    "滬韃": ("[loi extract]", "UNK"),
    "漯鷩穭": ("[loi extract]", "UNK"),
    "濟彥": ("[loi extract]", "UNK"),
    "濟績": ("Lu Khang", "L.Kha"),
    "炊憍": ("[loi extract]", "UNK"),
    "炊蝨": ("[loi extract]", "UNK"),
    "玄威": ("Ma Tieu", "M.Tie"),
    "玄德": ("Luu Bi", "Luu Bi"),
    "玷躁": ("[loi extract]", "UNK"),
    "理冷": ("[loi extract]", "UNK"),
    "瑜倉": ("[loi extract]", "UNK"),
    "璜穆": ("[loi extract]", "UNK"),
    "瓊嬰": ("Phung Nhuan", "P.Nhu"),
    "瓊就": ("Tran Cuu", "T.Cuu"),
    "盂咩": ("[loi extract]", "UNK"),
    "益遜": ("Gia Cat Khac", "G.CKh"),
    "瞻膜膜": ("[loi extract]", "UNK"),
    "砟蝸": ("[loi extract]", "UNK"),
    "磟茖": ("[loi extract]", "UNK"),
    "磥蝌": ("[loi extract]", "UNK"),
    "磭衈": ("[loi extract]", "UNK"),
    "祖詡": ("Vuong Lang", "W.Lang"),
    "祝融夫人": ("Phu nhan Chuc Dung", "ChucDung"),
    "秧蝜": ("[loi extract]", "UNK"),
    "稚叔": ("Truong Duong", "T.Du"),
    "穭蛻": ("[loi extract]", "UNK"),
    "空膍": ("[loi extract]", "UNK"),
    "竄蛣": ("[loi extract]", "UNK"),
    "緒術": ("Vien Thu", "V.Thu"),
    "翼德": ("Truong Phi", "T.Phi"),
    "聽藅": ("[loi extract]", "UNK"),
    "聽邦": ("[loi extract]", "UNK"),
    "脩于導": ("Vu Tu", "Vu Tu"),
    "臺樊": ("[loi extract]", "UNK"),
    "苳葆": ("[loi extract]", "UNK"),
    "茈悅": ("[loi extract]", "UNK"),
    "茠黖": ("[loi extract]", "UNK"),
    "葆祖": ("[loi extract]", "UNK"),
    "董荼奴": ("Dong Trac", "D.Trac"),
    "葵蔑": ("[loi extract]", "UNK"),
    "蓿坐": ("[loi extract]", "UNK"),
    "蘭宋": ("[loi extract]", "UNK"),
    "蝴娷": ("[loi extract]", "UNK"),
    "蟫傅": ("[loi extract]", "UNK"),
    "蠾鶞": ("[loi extract]", "UNK"),
    "言疆": ("Tuong Dong", "T.Do"),
    "越吉元帥": ("Viet Cat Nguyen soai", "VCatNS"),
    "遂高": ("Tuy Cao", "T.Cao"),
    "遠志": ("Trinh Vien Chi", "T.VChi"),
    "鄍翾": ("[loi extract]", "UNK"),
    "鄐撱": ("[loi extract]", "UNK"),
    "鄑粥": ("[loi extract]", "UNK"),
    "酈祀": ("[loi extract]", "UNK"),
    "酮衖": ("[loi extract]", "UNK"),
    "鉹螂": ("[loi extract]", "UNK"),
    "雅權": ("[loi extract]", "UNK"),
    "韞羃": ("[loi extract]", "UNK"),
    "顯奕": ("[loi extract]", "UNK"),
    "顯思": ("Vien Dam", "V.Dam"),
    "高盛": ("[loi extract]", "UNK"),
    "鴻豫": ("Chuong Tu", "C.Tu"),
    "鶪虜": ("[loi extract]", "UNK"),
    "鷩轗": ("[loi extract]", "UNK"),
    "黥漸": ("[loi extract]", "UNK"),
    "齯敻": ("[loi extract]", "UNK"),
    "龔襲": ("[loi extract]", "UNK"),
}

BIO_TRANSLATIONS: dict[str, tuple[str, str]] = {
    "下秦祚": ("[loi extract]", "UNK"),
    "不幸兵敗反被殺害": ("Khong may thua tran va bi giet", "Thua tran va bi giet"),
    "中諸葛瑾": ("Gia Cat Can", "G.CCan"),
    "互不侵犯": ("Khong xam pham lan nhau", "Khong xam pham"),
    "亦使待袁紹軍敗戰於官渡之戰而滅亡": ("Cung khien quan Vien Thieu thua o Quan Do va diet vong", "Khien Vien Thieu thua Quan Do diet vang"),
    "人恩飪": ("[loi extract]", "UNK"),
    "人物簡介": ("Gioi thieu nhan vat", "Gioi thieu"),
    "仁萵": ("[loi extract]", "UNK"),
    "仍東衝西突地解救被包圍的孫權和徐盛": ("Van xong pha cuu Ton Quyen va Tu Thanh bi vay", "Xong pha cuu Ton Quyen va Tu Thanh"),
    "他親率部下攻擊袁紹軍的本陣": ("Ong than danh quan Vien Thieu tai truong", "Than danh bon quan Vien Thieu"),
    "伐黃巾賊有功的忠臣之一": ("Mot trong nhung than cung co cong diet Tac Khuong", "Than cung co cong diet Tac Khuong"),
    "但因玄德離去和西涼邊境亂事": ("Nhung vi Luu Bi roi di va loan su o bien gioi Tay Luong", "Vi Luu Bi roi va bien gioi Tay Luong loan"),
    "但後來即為其智慧和謀略而折服": ("Nhung sau do bi su thong minh va muu luoc cua ong lam say me", "Sau bi tri tue va muu luoc lam say me"),
    "但後來感於曹操之得而歸順": ("Nhung sau cam phuc Tao Thao nen quy thuan", "Sau quy thuan vi cam phuc Tao Thao"),
    "但後來被關羽一刀刺於馬下而亡": ("Nhung sau bi Quan Vu mot dao giet tren ngua", "Bi Quan Vu mot dao giet"),
    "但是因他和叔父一樣反對曹操成為魏王": ("Nhung vi cung chu bac phan doi Tao Thao xung Vuong", "Phan doi Tao Thao xung Vuong nhu chu"),
    "但最後聽信賣國求榮楊松的話": ("Nhung cuoi cung tin loi Duong Tong ban nuoc cau vinh", "Tin Duong Tong ban nuoc cau vinh"),
    "但終不是袁紹對手而敗北身亡": ("Nhung cuoi cung khong phai doi thu cua Vien Thieu nen thua tran va chet", "Cuoi cung thua Vien Thieu va chet"),
    "使得曹操先斬了蔡瑁等水都督": ("Khien Tao Thao giet Thai Muu va thuy doc", "Tao Thao giet Thai Muu thuy doc"),
    "偶錟": ("[loi extract]", "UNK"),
    "六普通": ("[loi extract]", "UNK"),
    "兮硍": ("[loi extract]", "UNK"),
    "其巧": ("[loi extract]", "UNK"),
    "劉備交戰時屢建奇功": ("Khi giao chien voi Luu Bi lap nhieu cong lon", "Giao chien Luu Bi lap nhieu cong"),
    "劉璋": ("Luu Chuong", "L.Chu"),
    "力無": ("[loi extract]", "UNK"),
    "力諫馬要將軍隊駐紮於當道": ("Kien quyet khuyen Ma Ung phai dong quan o vi tri chan duong", "Khuyen Ma Ung dong quan chan duong"),
    "即掌控了魏國的實權": ("Nam quyen thuc te cua nha Nguoi", "Nam quyen thuc te nha Nguoi"),
    "即迫逼他在走七步內立即做一首詩": ("Bat buoc ong lam tho trong bay buoc", "Bat lam tho trong bay buoc"),
    "原本對年少的周瑜不服": ("Ban dau khong phuc Chu Du con tre", "Ban dau khong phuc Chu Du"),
    "原非臣所應議論者": ("Ban chat khong phai viec than nen ban", "Khong phai viec than nen ban"),
    "又強力主張與曹操長期抗戰": ("Lai manh me chu truong khang chien lau dai voi Tao Thao", "Chu truong khang chien lau dai voi Tao Thao"),
    "受孔明之命輔佐關羽治理荊州": ("Theo lenh Gia Cat Luong pho tro Quan Vu tri Kinh Chau", "Theo lenh K.M.Luong pho Quan Vu tri Kinh"),
    "司馬昭": ("Tu Ma Chieu", "T.Chieu"),
    "同盟": ("Lien minh dong minh", "Dong minh"),
    "吾軍兵糧短少": ("Quan ta thieu luong thao", "Thieu luong thao"),
    "和悟": ("[loi extract]", "UNK"),
    "因不願投降而北跪從容就義": ("Khong chiu dau hang quy huong bac tu an tu", "Khong dau hang quy huong bac tu an tu"),
    "因此在孔明臨死前遺言蔣琬接任蜀漢丞相大將軍": ("Nen truoc khi chet K.M.Luong di chuc Tuong Hoan lam thua tuong", "Di chuc Tuong Hoan lam thua tuong"),
    "因此在孫策臨死前曾遣言": ("Vi the truoc khi chet Ton Sach co di chuc", "Ton Sach truoc khi chet co di chuc"),
    "因為父親被甘寧射殺而深痛惡之": ("Vi cha bi Cam Ninh ban chet nen thu han sau sac", "Thu Cam Ninh vi cha bi ban chet"),
    "在劉備死後受到孔明的重用": ("Sau khi Luu Bi chet duoc Gia Cat Luong trong dung", "Sau Luu Bi chet duoc K.M.Luong dung"),
    "在劉備窮途末路時收容他": ("Khi Luu Bi cung duong tan cung thi cuu giup ong", "Cuu Luu Bi luc tan cung"),
    "在孔明北伐魏國時": ("Khi Gia Cat Luong bac phat nha Nguoi", "Khi K.M.Luong bac phat Nguoi"),
    "在官渡之戰中倒戈向曹操": ("Trong tran Quan Do phan sang phe Tao Thao", "Quan Do phan sang Tao Thao"),
    "在官渡之戰中投靠曹操": ("Trong tran Quan Do dau hang Tao Thao", "Quan Do dau hang Tao Thao"),
    "在曹操南下時投效曹操": ("Khi Tao Thao nam xuong thi dau hang phuc vu ong", "Tao Thao nam xuong thi dau hang"),
    "在曹操舉兵討伐董卓時加入曹操陣營中": ("Khi Tao Thao khoi binh danh Dong Trac thi gia nhap phe ong", "Gia nhap phe Tao Thao khi danh Dong Trac"),
    "在曹洪與曹仁守吳郡": ("Cung Tao Hong va Tao Nhan giu quan Ngo", "Cung Tao Hong Tao Nhan giu Ngo quan"),
    "在綿竹與黃忠戰得平分秋色": ("O Mien Truc giao chien voi Hoang Trung ngang tam", "O Mien Truc hoa Hoang Trung"),
    "在與關羽作戰時兵敗投降": ("Khi giao chien voi Quan Vu thi thua tran dau hang", "Giao chien Quan Vu thua roi dau hang"),
    "在艾": ("[loi extract]", "UNK"),
    "在董卓死後與李傕一起聯兵攻向長安": ("Sau khi Dong Trac chet lien quan Ly Tac danh Truong An", "Sau Dong Trac chet lien Ly Tac danh Truong An"),
    "在董卓被誅時亦同時被處死": ("Khi Dong Trac bi giet thi cung bi xu tu", "Cung bi xu khi Dong Trac chet"),
    "在關羽危急之時卻慫恿劉封不予以支援": ("Luc Quan Vu nguy cap lai xui Luu Phong khong cuu", "Xui Luu Phong khong cuu Quan Vu"),
    "在關羽被困麥城時突危到上庸搬救兵遭拒": ("Luc Quan Vu bi vay Mai Thanh den Thuong Dung cau vien bi tu choi", "Mai Thanh den Thuong Dung cau vien bi tu choi"),
    "在關羽被擒身亡之後": ("Sau khi Quan Vu bi bat va chet", "Sau Quan Vu bi bat chet"),
    "堅李儒": ("Ly Nhu", "L.Nhu"),
    "夫軍無習練": ("Quan doi khong luyen tap", "Quan khong luyen tap"),
    "失當乃國家動搖之本": ("Sai lam la goc re lam nuoc lung lay", "Sai lam lam nuoc lung lay"),
    "娃郈嚝僁嵽羺賑": ("[loi extract]", "UNK"),
    "孟達共謀欲迎劉備入蜀": ("Cung Manh Dat muu don Luu Bi vao Thuc", "Cung Manh Dat don Luu Bi vao Thuc"),
    "孫權相當賞識他的膽識與謀略": ("Ton Quyen rat danh gia cam dan va muu luoc cua ong", "Ton Quyen danh gia cam dan va muu luoc"),
    "將曹爽等人全部處死": ("Xu tu tat ca Tao Sang va nhung nguoi lien quan", "Xu tu Tao Sang va dong dang"),
    "對於曹操的作戰方式非常瞭解": ("Rat hieu ro cach danh tran cua Tao Thao", "Hieu ro cach danh cua Tao Thao"),
    "帕鶳": ("[loi extract]", "UNK"),
    "常擔任大使出使東吳": ("Thuong lam su gia den Dong Ngo", "Thuong lam su gia den Dong Ngo"),
    "常給予劉備許多資助": ("Thuong cap cho Luu Bi nhieu tien bac", "Thuong cap tien bac cho Luu Bi"),
    "建司馬師": ("Tu Ma Su", "T.M.Su"),
    "後中了楊彪之計與郭氾決裂": ("Sau trung ke Duong Bieu va Quach Phien chia re", "Trung ke Duong Bieu chia re Quach Phien"),
    "後來受袁譚攻擊而投靠曹操": ("Sau bi Vien Dam tan cong roi dau hang Tao Thao", "Bi Vien Dam tan cong roi dau Tao Thao"),
    "後來堅守雒城與劉備軍對壘": ("Sau kien tri giu Lac Thanh chong Luu Bi", "Giu Lac Thanh chong Luu Bi"),
    "後得到曹操的重視而轉投其帳下": ("Sau duoc Tao Thao trong dung roi chuyen sang phuc vu ong", "Duoc Tao Thao trong dung roi dau hang"),
    "徵之國必亂也": ("Neu dung nguoi nay nuoc chac loan", "Dung nguoi nay nuoc se loan"),
    "必能將士用命": ("Chac tuong si tan tam phuc vu", "Tuong si tan tam phuc vu"),
    "憑其三寸不爛之舌終使曹操打消此一念頭": ("Nho khau tai ba cuon khien Tao Thao bo y dinh do", "Khau tai khien Tao Thao bo y dinh"),
    "才晷": ("[loi extract]", "UNK"),
    "換頁": ("Chuyen trang", "Trang"),
    "於底秘": ("[loi extract]", "UNK"),
    "於是孔明決定南伐平定之": ("The Gia Cat Luong quyet dinh nam chinh binh dinh", "K.M.Luong quyet nam chinh binh dinh"),
    "於是暗中計劃迎劉備入蜀": ("Nen am muu don Luu Bi vao Thuc", "Am muu don Luu Bi vao Thuc"),
    "是曹操手下有名的參謀之一": ("La mot trong nhung mu si noi tieng cua Tao Thao", "Mu si noi tieng cua Tao Thao"),
    "曹操因中計殺掉蔡瑁和張允": ("Tao Thao trung ke giet Thai Muu va Truong Van", "Trung ke giet Thai Muu va Truong Van"),
    "曾三番兩次扮演使者出使蜀漢": ("Tung nhieu lan lam su gia den Thuc Han", "Nhieu lan lam su gia den Thuc"),
    "曾偕同馬騰攻擊長安的李傕": ("Tung cung Ma Dang tan cong Ly Tac o Truong An", "Cung Ma Dang danh Ly Tac Truong An"),
    "曾在曹丕征吳時打敗曹休": ("Tung danh bai Tao Tu khi Tao Phi chinh Ngo", "Danh bai Tao Tu khi Tao Phi chinh Ngo"),
    "曾給予關羽正確良好的建言": ("Tung dua ra loi khuyen dung dan cho Quan Vu", "Tung khuyen Quan Vu dung dan"),
    "曾與吳國名將陸遜之子陸抗在襄陽對抗為敵": ("Tung dich thu voi Luc Kang con cua Luc Ton o Tuong Duong", "Dich thu Luc Kang tai Tuong Duong"),
    "最後為顧人民福祇而開城投降": ("Cuoi cung vi dan chung ma mo thanh dau hang", "Vi dan chung ma mo thanh dau hang"),
    "最後被張飛斬於刀下": ("Cuoi cung bi Truong Phi chem chet", "Bi Truong Phi chem chet"),
    "有感於其奸詐冷酷而離開他": ("Cam thay ong gian xao lanh lung nen roi bo", "Roi bo vi gian xao lanh lung"),
    "有限之金集無用之兵": ("Tien co han tap quan vo dung", "Tien han tap quan vo dung"),
    "末捧": ("[loi extract]", "UNK"),
    "此人必不負主公之期望": ("Nguoi nay chac khong phu mong doi cua chu cong", "Khong phu mong doi chu cong"),
    "此城將臨屠馬以食": ("Thanh nay sap giet ngua de an", "Sap giet ngua de an"),
    "氣請選擇要偵查的目標郡縣": ("Hay chon quan huyen muc tieu do tham", "Chon quan huyen do tham"),
    "氶親密": ("[loi extract]", "UNK"),
    "汗族": ("[loi extract]", "UNK"),
    "為報父仇而與東吳交戰": ("Vi bao thu cha ma giao chien voi Dong Ngo", "Bao thu cha giao chien Dong Ngo"),
    "為東吳三朝元老": ("La nguyen lao ba doi cua Dong Ngo", "Nguyen lao ba doi Dong Ngo"),
    "為秉": ("[loi extract]", "UNK"),
    "狹馬騰": ("[loi extract]", "UNK"),
    "王朗": ("Vuong Lang", "W.Lang"),
    "瓣孔融": ("[loi extract]", "UNK"),
    "田豐": ("Dien Phong", "D.Pho"),
    "由巧": ("[loi extract]", "UNK"),
    "由於施行仁政": ("Nho thi hanh chinh nhan ai", "Nho thi hanh chinh nhan ai"),
    "當他得知蔡瑁欲暗殺劉備時": ("Khi biet Thai Muu dinh am sat Luu Bi", "Biet Thai Muu dinh am sat Luu Bi"),
    "當初劉備要收養他時": ("Luc dau Luu Bi dinh nhan nuoi ong", "Luu Bi dinh nhan nuoi ong"),
    "的膨": ("[loi extract]", "UNK"),
    "的觼": ("[loi extract]", "UNK"),
    "知瓣藗": ("[loi extract]", "UNK"),
    "竣撣": ("[loi extract]", "UNK"),
    "終於使呂布殺掉董卓": ("Cuoi cung khien Lu Bo giet Dong Trac", "Khien Lu Bo giet Dong Trac"),
    "終於夠因曹操嫉妒而被斬首": ("Cuoi cung bi Tao Thao ghen tuong ma chem dau", "Bi Tao Thao ghen tuong chem dau"),
    "終於結束紛擾的三國亂世": ("Cuoi cung ket thuc thoi loan lac Tam Quoc", "Ket thuc loan lac Tam Quoc"),
    "統萬眾必有所失": ("Chi huy van quan tat co sai sot", "Chi huy van quan co sai sot"),
    "經夏侯惇引薦而為曹操重用": ("Duoc Ha Hau Don gioi thieu nen Tao Thao trong dung", "Ha Hau Don gioi thieu duoc Tao Thao dung"),
    "繼承將軍權位": ("Ke thua quyen luc tuong quan", "Ke thua quyen tuong quan"),
    "而將徐州讓給劉備管理": ("Va nhuong Xu Chau cho Luu Bi quan ly", "Nhuong Xu Chau cho Luu Bi"),
    "臨曲": ("[loi extract]", "UNK"),
    "自曹操舉兵開始便追隨曹操": ("Tu khi Tao Thao khoi binh da theo ong", "Theo Tao Thao tu khi khoi binh"),
    "與蔡瑁等人共同把持荊州的實權": ("Cung Thai Muu nam quyen thuc te Kinh Chau", "Cung Thai Muu nam quyen Kinh Chau"),
    "與釧": ("[loi extract]", "UNK"),
    "與顏良同為響噹噹的猛將": ("Cung Nhan Luong la mot trong nhung tuong hung manh tieng tam", "Cung Nhan Luong la tuong hung manh"),
    "若明公令一上將為太守": ("Neu minh cong cu mot tuong lam thai thu", "Neu cu tuong lam thai thu"),
    "茈緊張": ("[loi extract]", "UNK"),
    "萵銢": ("[loi extract]", "UNK"),
    "董角": ("Dong Trac", "D.Trac"),
    "蔡瑁": ("Thai Muu", "T.Muu"),
    "蝘囃": ("[loi extract]", "UNK"),
    "行釦灅": ("[loi extract]", "UNK"),
    "許攸": ("Tu Vien", "T.Vien"),
    "請選擇擔任搜尋人才的武將": ("Hay chon tuong phu trach tim kiem nhan tai", "Chon tuong tim nhan tai"),
    "諸葛亮曾在他的出師表讚美向寵才能": ("Gia Cat Luong trong Bieu chinh tac ca nang tai cua Huong Sung", "K.M.Luong ca ngoi tai nang Huong Sung"),
    "谷費褘": ("[loi extract]", "UNK"),
    "赴葭": ("[loi extract]", "UNK"),
    "足以長期與敵互角於山野之間": ("Du suc chien lau dai voi dich tren nui rung", "Du suc chien lau dai tren nui"),
    "跼良好": ("[loi extract]", "UNK"),
    "迫郭氾": ("[loi extract]", "UNK"),
    "部陽": ("[loi extract]", "UNK"),
    "馬炎": ("[loi extract]", "UNK"),
    "鴽僂": ("[loi extract]", "UNK"),
    "齒睄": ("[loi extract]", "UNK"),
}

MENU_JSON = ROOT / "translations" / "extracted" / "menu.json"
BIO_JSON = ROOT / "translations" / "extracted" / "bio.json"

ASCII_RE = re.compile(r"[^a-zA-Z0-9 ]")
VALID_ABBREV_RE = re.compile(r"^[A-Za-z0-9 ]+$")


def fit_abbrev(text: str, ascii_max: int) -> str:
    """Return ASCII-only abbrev (a-z A-Z 0-9 space) with len <= ascii_max."""
    cleaned = ASCII_RE.sub("", text).strip()
    if not cleaned:
        return "UNK"[:ascii_max]
    if len(cleaned) <= ascii_max:
        return cleaned

    nospace = cleaned.replace(" ", "")
    if len(nospace) <= ascii_max:
        return nospace

    words = cleaned.split()
    if len(words) >= 2:
        # "Trieu Van" -> "T Van", "Dien Phong" -> "D Phong"
        initial = words[0][0]
        rest = " ".join(words[1:])
        candidate = f"{initial} {rest}"
        if len(candidate) <= ascii_max:
            return candidate
        candidate = f"{initial}{rest.replace(' ', '')}"
        if len(candidate) <= ascii_max:
            return candidate
        # initials only: "Tu Ma Y" -> "TMY"
        initials = "".join(w[0] for w in words if w)
        if len(initials) <= ascii_max:
            return initials

    return nospace[:ascii_max]


def is_garbled(translated: str) -> bool:
    return translated == "[loi extract]"


def translate_entry(original: str, mapping: dict[str, tuple[str, str]], ascii_max: int) -> tuple[str, str]:
    if original not in mapping:
        raise KeyError(f"no mapping for {original!r}")
    translated, abbrev_hint = mapping[original]
    if is_garbled(translated):
        return translated, fit_abbrev("UNK", ascii_max)
    abbrev = fit_abbrev(abbrev_hint, ascii_max)
    if len(abbrev) > ascii_max:
        abbrev = fit_abbrev(translated, ascii_max)
    return translated, abbrev


def validate_entry(entry: dict, *, label: str) -> list[str]:
    errors: list[str] = []
    abbrev = entry.get("abbrev", "")
    translated = entry.get("translated", "")
    ascii_max = entry.get("ascii_max", 0)
    entry_id = entry.get("id", "?")

    if entry.get("status") != "done":
        errors.append("status not done")
    if not translated:
        errors.append("empty translated")
    if not abbrev:
        errors.append("empty abbrev")
    if ASCII_RE.search(abbrev) or not VALID_ABBREV_RE.match(abbrev):
        errors.append(f"non-ASCII abbrev {abbrev!r}")
    if len(abbrev) > ascii_max:
        errors.append(f"abbrev len {len(abbrev)} > ascii_max {ascii_max}")
    if is_garbled(translated):
        if translated != "[loi extract]" or abbrev != "UNK":
            errors.append("garbled must be [loi extract]/UNK")
    return [f"[{label}] {entry_id} ({entry.get('original', '')!r}): {e}" for e in errors]


def apply_file(
    path: Path,
    mapping: dict[str, tuple[str, str]],
    *,
    dry_run: bool,
    force: bool = False,
) -> tuple[int, int, list[str]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    applied = 0
    skipped = 0
    errors: list[str] = []

    for entry in data:
        if (
            not force
            and entry.get("status") == "done"
            and entry.get("translated")
        ):
            skipped += 1
            continue

        original = entry["original"]
        try:
            translated, abbrev = translate_entry(original, mapping, entry["ascii_max"])
        except KeyError as exc:
            errors.append(f"{path.name}: {exc}")
            continue

        entry["translated"] = translated
        entry["abbrev"] = abbrev
        entry["status"] = "done"
        applied += 1
        errors.extend(validate_entry(entry, label=path.name))

    if not dry_run and not any("no mapping" in e or "status not" in e for e in errors):
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")

    return applied, skipped, errors


def verify_all_done(path: Path) -> list[str]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    problems: list[str] = []
    for entry in data:
        problems.extend(validate_entry(entry, label=path.name))
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing JSON")
    parser.add_argument("--menu-only", action="store_true")
    parser.add_argument("--bio-only", action="store_true")
    parser.add_argument("--force", action="store_true", help="Re-apply even if already done")
    args = parser.parse_args()

    targets: list[tuple[Path, dict[str, tuple[str, str]]]] = []
    if not args.bio_only:
        targets.append((MENU_JSON, MENU_TRANSLATIONS))
    if not args.menu_only:
        targets.append((BIO_JSON, BIO_TRANSLATIONS))

    total_applied = 0
    total_skipped = 0
    all_errors: list[str] = []

    for path, mapping in targets:
        applied, skipped, errors = apply_file(path, mapping, dry_run=args.dry_run, force=args.force)
        total_applied += applied
        total_skipped += skipped
        all_errors.extend(errors)
        print(f"{path.name}: applied={applied} skipped={skipped} validation_issues={len(errors)}")

    if all_errors:
        print("\nErrors:")
        for err in all_errors:
            print(f"  {err}")
        return 1

    if not args.dry_run:
        for path, _ in targets:
            post = verify_all_done(path)
            if post:
                print(f"\nPost-check failed for {path.name}:")
                for err in post:
                    print(f"  {err}")
                return 1

    pending_menu = sum(1 for _ in [])  # placeholder
    with MENU_JSON.open(encoding="utf-8") as f:
        menu_data = json.load(f)
    with BIO_JSON.open(encoding="utf-8") as f:
        bio_data = json.load(f)
    pending_menu = sum(1 for e in menu_data if e.get("status") != "done")
    pending_bio = sum(1 for e in bio_data if e.get("status") != "done")
    garbled_menu = sum(1 for e in menu_data if e.get("translated") == "[loi extract]")
    garbled_bio = sum(1 for e in bio_data if e.get("translated") == "[loi extract]")

    print(
        f"\nOK: applied={total_applied} skipped={total_skipped} "
        f"pending_menu={pending_menu} pending_bio={pending_bio} "
        f"garbled_menu={garbled_menu} garbled_bio={garbled_bio}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
