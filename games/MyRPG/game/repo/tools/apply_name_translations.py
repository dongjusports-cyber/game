#!/usr/bin/env python3
"""Apply Vietnamese translations to pending name.json entries (indices 240-619)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME_JSON = ROOT / "translations" / "extracted" / "name.json"

START_IDX = 240
END_IDX = 619  # inclusive

WEAPON_PREFIXES = "戟矛脊門釭鞭龍斧蒺"
FACTION_PREFIXES = "馬何王"

# Characters that indicate garbled / corrupt extraction (not valid name text).
GARBLED_CHARS = set(
    "吨悀悜穭茈捊鷇髐椌貜壑麭悁悕悝顐蘅戙狺抔覽蠾菾蒂蒔糷盒扆狗膳悜爬隍爸溯嬤鶗椌閉茖魴昕倉沮鷇"
)

ASCII_RE = re.compile(r"[^a-zA-Z0-9 .]")

# (translated, abbrev_hint) — abbrev_hint may be longer than ascii_max; fit_abbrev trims.
EXACT: dict[str, tuple[str, str]] = {
    # Courtesy names (字)
    "叔治": ("Lu Chi", "Lu Chi"),
    "仲宣": ("Vuong Can", "V.Can"),
    "文舒": ("Cam Thao", "C.Thao"),
    "孔碩": ("Khong Thuc", "K.Thu"),
    "玄沖": ("Cam Hoan", "C.Hoa"),
    "仲業": ("Cung Hy", "C.Hy"),
    "菾階": ("[loi extract]", "UNK"),
    "公緒": ("Gia Khong", "G.Kho"),
    "次曾": ("Khong Nhung", "K.Nhu"),
    "思潛": ("Tu Lam", "T.Lam"),
    "木鹿": ("Doc Loc", "D.Loc"),
    "伯達": ("Tu Ma Lang", "TMLang"),
    "仲達": ("Tu Ma Y", "TuMaY"),
    "叔達": ("Tu Ma Phu", "T.Ph"),
    "義望": ("Lu Nong", "L.Ng"),
    # Books / items
    "孫子兵法": ("Ton Tu binh phap", "Ton Tu"),
    "孟德新書": ("Man Duc tan thu", "Man Duc"),
    "穭茈限": ("[loi extract]", "UNK"),
    "奇門遁甲天書": ("Ky Mon dun giap thien thu", "KMDG thien thu"),
    "將遁甲天書": ("Tuong dun giap thien thu", "Tuong dun giap"),
    "弩青囊書": ("Nu thanh nang thu", "Nu TN thu"),
    "雜病論": ("Ta benh luan", "Ta benh luan"),
    # Horses
    "赤兔馬": ("Xich Tho", "Xich Tho"),
    "的蘆": ("De Lu", "De Lu"),
    "穭鷇嶺號": ("[loi extract]", "UNK"),
    "蒂戊": ("[loi extract]", "UNK"),
    "烏馬": ("O Ma", "O Ma"),
    "捲毛赤兔馬": ("Xich Tho cuon mao", "XT cuon mao"),
    "黃驃馬": ("Hoang bieu ma", "H.bieu ma"),
    "蒔糷": ("[loi extract]", "UNK"),
    # Weapons
    "大刀": ("Dao lon", "D.lon"),
    "大砍刀": ("Dao khan lon", "Dao khan"),
    "三尖刀": ("Tam thien dao", "Tam thien"),
    "日月刀": ("Nhat nguyet dao", "N.nguyet"),
    "截頭大刀": ("Cat dau dao lon", "Cat dau"),
    "星寶刀": ("Tinh bao dao", "Tinh bao"),
    "門三尖兩刃刀": ("Tam thien luong nhan dao", "Tam thien LN"),
    "青釭劍": ("Thanh Cuong", "Thanh Cuo"),
    "悜吨捊": ("[loi extract]", "UNK"),
    "雙股劍": ("Song cot kiem", "Song cot"),
    "鐵鞭": ("Thiet bien", "Thiet bien"),
    "青龍偃月刀": ("Q.Long yen nguyet dao", "Q.Long dao"),
    "山大斧": ("Son dai phu", "Son dai phu"),
    "遙蘸金斧": ("[loi extract]", "UNK"),
    "鐵鎚": ("Thiet chuy", "Thiet chuy"),
    "鐵蒺蔾骨朵": ("Thiet tich le co do", "Thiet TL"),
    "鐵鎗": ("Thiet thuong", "Thiet thuong"),
    "畫戟": ("Hoa Ke", "Hoa K"),
    "雙鐵戟": ("Song thiet ke", "Song thiet"),
    "方天畫戟": ("Phuong Thien Ke", "P.Thien Ke"),
    "丈八蛇矛": ("Truong Bat Mao", "T.Bat Mao"),
    "脊蛇矛": ("Xa mao", "Xa mao"),
    "門飛叉": ("Phi xa", "Phi xa"),
    "玉璽": ("Ngoc ty", "Ngoc ty"),
    # Prefix-corrupted names (weapon prefix + person)
    "釭丁原": ("Dinh Nguyen", "D.Nguyen"),
    "吨悀": ("[loi extract]", "UNK"),
    "貜悀": ("[loi extract]", "UNK"),
    "鞭丁儀": ("Dinh Nghi", "D.Nghi"),
    "龍丁序": ("Dinh Tu", "D.Tu"),
    "鷇壑": ("[loi extract]", "UNK"),
    "斧于詮": ("Vu Toan", "V.Toan"),
    "椌髐": ("[loi extract]", "UNK"),
    "蒺王子服": ("Tu Phuc", "Tu Phuc"),
    # Wang family / generals
    "王允": ("Vuong Ung", "V.Ung"),
    "王方": ("Vuong Phuong", "V.Ph"),
    "王平": ("Vuong Binh", "V.Binh"),
    "王伉": ("Vuong Khang", "V.Khang"),
    "戟王匡": ("Vuong Khoang", "V.Khoang"),
    "王甫": ("Vuong Phu", "V.Phu"),
    "矛王忠": ("Vuong Trung", "V.Trung"),
    "脊王昌": ("Vuong Xuong", "V.Xuong"),
    "門王則": ("Vuong Tac", "V.Tac"),
    "王垢": ("Vuong Cau", "V.Cau"),
    "釭王威": ("Vuong Uy", "V.Uy"),
    "鞭王基": ("Vuong Co", "V.Co"),
    "龍王累": ("Vuong Loi", "V.Loi"),
    "斧王雙": ("Vuong Song", "V.Song"),
    "蒺王必": ("Vuong Tat", "V.Tat"),
    "王連": ("Vuong Lien", "V.Lien"),
    "王昶": ("Vuong Suong", "V.Suong"),
    "王肅": ("Vuong Tuc", "V.Tuc"),
    "王經": ("Vuong Kinh", "V.Kinh"),
    "戟王瓘": ("Vuong Quan", "V.Quan"),
    "王真": ("Vuong Chan", "V.Chan"),
    "矛王含": ("Vuong Ham", "V.Ham"),
    "脊王頎": ("Vuong Hy", "V.Hy"),
    "門王祥": ("Vuong Huong", "V.Huong"),
    "王渾": ("Vuong Hon", "V.Hon"),
    "釭王戎": ("Vuong Nhung", "V.Nhung"),
    "吨悀蔭": ("[loi extract]", "UNK"),
    "悀蔭": ("[loi extract]", "UNK"),
    "公孫修": ("Cong Ton Tu", "C.Ton Tu"),
    "公孫恭": ("Cong Ton Cung", "C.Ton Cung"),
    "炊蔭": ("[loi extract]", "UNK"),
    "壑蔭": ("[loi extract]", "UNK"),
    "礞蔭": ("[loi extract]", "UNK"),
    "韙敻": ("[loi extract]", "UNK"),
    "蒺文聘": ("Van Binh", "V.Binh"),
    "文醜": ("Van Xau", "Van Xau"),
    "卞喜": ("Bien Hi", "B.Hi"),
    "毋丘儉": ("Vo Khu Kiem", "Vo Khu K"),
    "毋丘甸": ("Vo Khu Dien", "Vo Khu D"),
    "毛玠": ("Mao Gioi", "M.Gioi"),
    "太史慈": ("Thai Su Tu", "T.Su Tu"),
    "脊孔怞": ("Khong Uu", "K.Uu"),
    "門孔秀": ("Khong Tu", "K.Tu"),
    "方悅": ("Phuong Duyet", "P.Duyet"),
    "釭尹奉": ("Doan Phung", "D.Phung"),
    "尹默": ("Doan Mac", "D.Mac"),
    "尹禮": ("Doan Le", "D.Le"),
    "炊角": ("[loi extract]", "UNK"),
    "壑麭壑": ("[loi extract]", "UNK"),
    # Sima clan
    "司馬炎": ("Tu Ma Viem", "TM Viem"),
    "馬昭": ("Tu Ma Chieu", "TM Chieu"),
    "司馬師": ("Tu Ma Su", "TM Su"),
    "馬朗": ("Tu Ma Lang", "TM Lang"),
    "司馬懿": ("Tu Ma Y", "TuMaY"),
    "司馬孚": ("Tu Ma Phu", "TM Phu"),
    "司馬望": ("Tu Ma Vong", "TM Vong"),
    "司馬攸": ("Tu Ma Du", "TM Du"),
    "司馬佃": ("Tu Ma Dien", "TM Dien"),
    "史渙": ("Su Hoan", "S.Hoan"),
    "脊左靈": ("Ta Linh", "T.Linh"),
    "門左咸": ("Ta Ham", "T.Ham"),
    "甘寧": ("Cam Ninh", "C.Ninh"),
    "釭田章": ("Dien Chuong", "D.Chuong"),
    "田續": ("Dien Tuc", "D.Tuc"),
    "田楷": ("Dien Khai", "D.Khai"),
    "王句安": ("Cau An", "C.An"),
    "馬石苞": ("Thach Bao", "T.Bao"),
    "馬丘建": ("Khu Kien", "K.Kien"),
    "馬伊籍": ("Y Te", "Y.Te"),
    "馬伍習": ("Ngu Tap", "N.Tap"),
    "馬伍瓊": ("Ngu Quynh", "N.Quynh"),
    "伍延": ("Ngu Diem", "N.Diem"),
    "任峻": ("Nham Tuan", "N.Tuan"),
    "全琮": ("Toan Tong", "T.Tong"),
    "全懌": ("Toan Dich", "T.Dich"),
    "全端": ("Toan Doan", "T.Doan"),
    "脊全紀": ("Toan Ky", "T.Ky"),
    "門向朗": ("Huong Lang", "H.Lang"),
    "向寵": ("Huong Sung", "H.Sung"),
    "釭成宜": ("Thanh Nghi", "T.Nghi"),
    "吨悁邢": ("[loi extract]", "UNK"),
    "成濟": ("Thanh Te", "T.Te"),
    "朱光": ("Chu Quang", "C.Quang"),
    "爬隍": ("[loi extract]", "UNK"),
    "王朱然": ("Chu Nhien", "C.Nhien"),
    "馬朱雋": ("Chu Tuan", "C.Tuan"),
    "馬朱褒": ("Chu Bao", "C.Bao"),
    "馬朱靈": ("Chu Linh", "C.Linh"),
    "馬朱讚": ("Chu Tan", "C.Tan"),
    "馬朱異": ("Chu Di", "C.Di"),
    "羊祜": ("Duong Ho", "D.Ho"),
    "吉太": ("Cat Thai", "C.Thai"),
    "吉邈": ("Cat Dieu", "C.Dieu"),
    "吉穆": ("Cat Mac", "C.Mac"),
    "汪昭": ("Vuong Chieu", "V.Chieu"),
    "脊忙牙長": ("Mang Nha Truong", "M.Nha Truong"),
    "蠾騥": ("[loi extract]", "UNK"),
    "何儀": ("Ha Nghi", "H.Nghi"),
    "釭何曼": ("Ha Man", "H.Man"),
    "何曾": ("Ha Tang", "H.Tang"),
    "冷苞": ("Lanh Bao", "L.Bao"),
    "子蘭": ("Tu Lan", "T.Lan"),
    "馬吳敦": ("Ngo Don", "N.Don"),
    "馬吳景": ("Ngo Canh", "N.Canh"),
    "馬吳碩": ("Ngo Thac", "N.Thac"),
    "馬吳質": ("Ngo Chat", "N.Chat"),
    "馬吳蘭": ("Ngo Lan", "N.Lan"),
    "吳懿": ("Ngo Nghi", "N.Nghi"),
    "吳粲": ("Ngo Sam", "N.Sam"),
    "吳綱": ("Ngo Cuong", "N.Cuong"),
    "呂布": ("Lu Bo", "Lu Bo"),
    "呂公": ("Lu Cong", "L.Cong"),
    "威璜": ("Uy Hoang", "U.Hoang"),
    "呂常": ("Lu Thuong", "L.Thuong"),
    "釭呂凱": ("Lu Khai", "L.Khai"),
    "吨悝": ("[loi extract]", "UNK"),
    "呂蒙": ("Lu Mong", "L.Mong"),
    "呂範": ("Lu Pham", "L.Pham"),
    "馬宋忠": ("Tong Trung", "T.Trung"),
    "馬宋果": ("Tong Qua", "T.Qua"),
    "馬宋憲": ("Tong Hien", "T.Hien"),
    "馬宋謙": ("Tong Khiem", "T.Khiem"),
    "馬宋寶": ("Tong Bao", "T.Bao"),
    "岑昏": ("Sam Hon", "S.Hon"),
    "岑壁": ("Sam Bich", "S.Bich"),
    "岑威": ("Sam Uy", "S.Uy"),
    "李別": ("Ly Biet", "L.Biet"),
    "李孚": ("Ly Phu", "L.Phu"),
    "李珪": ("Ly Khu", "L.Khu"),
    "釭李異": ("Ly Di", "L.Di"),
    "吨悝麚": ("[loi extract]", "UNK"),
    "李肅": ("Ly Tuc", "L.Tuc"),
    "李蒙": ("Ly Mong", "L.Mong"),
    "馬李豐": ("Ly Phong", "L.Phong"),
    "馬李嚴": ("Ly Nghiem", "L.Nghiem"),
    "馬李傕": ("Ly Thoat", "L.Thoat"),
    "馬李伏": ("Ly Phuc", "L.Phuc"),
    "馬李輔": ("Ly Pho", "L.Pho"),
    "李勝": ("Ly Thang", "L.Thang"),
    "李歆": ("Ly Ham", "L.Ham"),
    "李鵬": ("Ly Bang", "L.Bang"),
    "杜襲": ("Do Tap", "D.Tap"),
    "杜預": ("Do Du", "D.Du"),
    "摩可": ("Ma Kha", "M.Kha"),
    "沈瑩": ("Tham Ung", "T.Ung"),
    "釭車冑": ("Xa Cau", "X.Cau"),
    "辛毘": ("Tan Ty", "T.Ty"),
    "辛敞": ("Tan Thuong", "T.Thuong"),
    "爸溯": ("[loi extract]", "UNK"),
    "嬤楹": ("[loi extract]", "UNK"),
    "馬朵思大王": ("Doc Loc dai vuong", "Doc Loc"),
    "典韋": ("Dien Vi", "D.Vi"),
    "典滿": ("Dien Man", "D.Man"),
    "鶗顐蘅": ("[loi extract]", "UNK"),
    "卑衍": ("Ti Vien", "T.Vien"),
    "和洽": ("Hoa Hiep", "H.Hiep"),
    "周昕": ("Chu Tan", "C.Tan"),
    "周倉": ("Chu Thuong", "C.Thuong"),
    "周泰": ("Chu Thai", "C.Thai"),
    "周群": ("Chu Quan", "C.Quan"),
    "釭周平": ("Chu Binh", "C.Binh"),
    "吨悕": ("[loi extract]", "UNK"),
    "孟坦": ("Man Dam", "M.Dam"),
    "孟達": ("Man Dat", "M.Dat"),
    "馬尚舉": ("Thuong Cuu", "T.Cuu"),
    "王武安國": ("Vo An Quoc", "V.An Quoc"),
    "沮鵠": ("Tu Hoac", "T.Hoac"),
    "金旋": ("Kim Tuyen", "K.Tuyen"),
    "金環三結": ("Kim Hoan tam ket", "Kim Hoan"),
    "昕金禕": ("[loi extract]", "UNK"),
    "倉阿會喃": ("[loi extract]", "UNK"),
    "善昌稀": ("[loi extract]", "UNK"),
    "瑜昌奇": ("[loi extract]", "UNK"),
    "魴慮": ("[loi extract]", "UNK"),
    "宗預": ("Tong Du", "T.Du"),
    "釭羌王迷": ("Cuong Vuong Mi", "C.V.Mi"),
    "封諝": ("Phong Tien", "P.Tien"),
    "侯覽": ("Hau Lam", "H.Lam"),
    "馬姜維": ("Khuong Duy", "K.Duy"),
    "王柳甫": ("Lieu Phu", "L.Phu"),
    "閉茖": ("[loi extract]", "UNK"),
    "紀靈": ("Ky Linh", "K.Linh"),
    "胡才": ("Ho Tai", "H.Tai"),
    "胡赤兒": ("Ho Xich Nhi", "H.Xich Nhi"),
    "車兒": ("Xa Nhi", "X.Nhi"),
    "寶胡遵": ("Ho Ton", "H.Ton"),
    "胡烈": ("Ho Liet", "H.Liet"),
    "胡淵": ("Ho Uyen", "H.Uyen"),
    "胡奮": ("Ho Phan", "H.Phan"),
    "釭范疆": ("Pham Cuong", "P.Cuong"),
    "戙玷臚狺": ("[loi extract]", "UNK"),
    "抔平": ("[loi extract]", "UNK"),
    "覽卻正": ("[loi extract]", "UNK"),
    "成俄何燒戈": ("[loi extract]", "UNK"),
    "馬韋晃": ("Vi Hoang", "V.Hoang"),
    "王倫直": ("Luon Truc", "L.Truc"),
    "夏惲": ("Ha Van", "H.Van"),
    "夏恂": ("Ha Tuan", "H.Tuan"),
    "夏侯玄": ("Ha Hau Huyen", "HH Huyen"),
    "侯存": ("Hau Ton", "H.Ton"),
    "夏侯尚": ("Ha Hau Thuong", "HH Thuong"),
    "夏侯威": ("Ha Hau Uy", "HH Uy"),
    "夏侯恩": ("Ha Hau An", "HH An"),
    "夏侯惇": ("Ha Hau Don", "HH Don"),
    "夏侯淵": ("Ha Hau Vien", "HH Vien"),
    "侯惠": ("Hau Hue", "H.Hue"),
    "侯德": ("Hau Duc", "H.Duc"),
    "侯蘭": ("Hau Lan", "H.Lan"),
    "夏侯霸": ("Ha Hau Ba", "HH Ba"),
    "夏侯楙": ("Ha Hau Mao", "HH Mao"),
    "何孫仲": ("Ton Trung", "T.Trung"),
    "馬孫匡": ("Ton Khoang", "T.Khoang"),
    "王孫秀": ("Ton Tu", "T.Tu"),
    "孫朗": ("Ton Lang", "T.Lang"),
    "孫桓": ("Ton Hoan", "T.Hoan"),
    "孫乾": ("Ton Can", "T.Can"),
    "孫皓": ("Ton Hao", "T.Hao"),
    "孫策": ("Ton Sach", "T.Sach"),
    "孫瑜": ("Ton Nhu", "T.Nhu"),
    "孫韶": ("Ton Thieu", "T.Thieu"),
    "孫冀": ("Ton Ky", "T.Ky"),
    "孫觀": ("Ton Quan", "T.Quan"),
    "孫翊": ("Ton At", "T.At"),
    "何孫皎": ("Ton Kieu", "T.Kieu"),
    "馬孫琳": ("Ton Lam", "T.Lam"),
    "王孫歆": ("Ton Ham", "T.Ham"),
    "徐商": ("Tu Thuong", "T.Thuong"),
    "徐庶": ("Tu Thuc", "T.Thuc"),
    "徐盛": ("Tu Thinh", "T.Thinh"),
    "宴明": ("Yen Minh", "Y.Minh"),
    "桓楷": ("Hoan Khai", "H.Khai"),
    "桓範": ("Hoan Pham", "H.Pham"),
    "祖茂": ("To Mao", "T.Mao"),
    "祖弼": ("To Tat", "T.Tat"),
    "狗釣": ("[loi extract]", "UNK"),
    "戙陬": ("[loi extract]", "UNK"),
    "秦宓": ("Tan Mat", "T.Mat"),
    "秦明": ("Tan Minh", "T.Minh"),
    "膳晡": ("[loi extract]", "UNK"),
    "何耿紀": ("Cam Ky", "C.Ky"),
    "馬荀爽": ("Tuan Sang", "T.Sang"),
    "王荀諶": ("Tuan Than", "T.Than"),
    "荀正": ("Tuan Chinh", "T.Chinh"),
    "荀顗": ("Tuan Nghiem", "T.Nghiem"),
    "袁尚": ("Vien Thuong", "V.Thuong"),
    "袁術": ("Vien Thuat", "V.Thuat"),
    "袁熙": ("Vien Hy", "V.Hy"),
    "袁譚": ("Vien Dam", "V.Dam"),
    "袁遺": ("Vien Di", "V.Di"),
    "郝昭": ("Hac Chieu", "H.Chieu"),
    "扆豕": ("[loi extract]", "UNK"),
    "馬岱": ("Ma Dai", "Ma Dai"),
    "馬延": ("Ma Diem", "M.Diem"),
    "何馬玩": ("Ma Hoan", "M.Hoan"),
    "馬馬漢": ("Ma Han", "Ma Han"),
    "王馬遵": ("Ma Ton", "M.Ton"),
    "馬謖": ("Ma Tuc", "M.Tuc"),
    "馬元義": ("Ma Nguyen Nghia", "M.NgNghia"),
    "馬邈": ("Ma Dieu", "M.Dieu"),
    "盒邑": ("[loi extract]", "UNK"),
    "高定": ("Cao Dinh", "C.Dinh"),
    "高順": ("Cao Thuan", "C.Thuan"),
    "高幹": ("Cao Can", "C.Can"),
    "高覽": ("Cao Lam", "C.Lam"),
    "高昇": ("Cao Thang", "C.Thang"),
    "悜藀": ("[loi extract]", "UNK"),
    "悜薽": ("[loi extract]", "UNK"),
    "烏桓觸": ("O Hoan Xuc", "O.H.Xuc"),
    "師纂": ("Su Toan", "S.Toan"),
    "何崔琰": ("Thoi Nghiem", "T.Nghiem"),
    "馬崔諒": ("Thoi Luong", "T.Luong"),
    "王張角": ("Truong Giac", "T.Giac"),
    "張讓": ("Truong Nhuong", "T.Nhuong"),
    "張武": ("Truong Vu", "T.Vu"),
    "張允": ("Truong Doan", "T.Doan"),
    "張先": ("Truong Tien", "T.Tien"),
    "張承": ("Truong Thua", "T.Thua"),
    "張松": ("Truong Tong", "T.Tong"),
    "張虎": ("Truong Ho", "T.Ho"),
    "張南": ("Truong Nam", "T.Nam"),
    "張郃": ("Truong Hach", "T.Hach"),
    "張飛": ("Truong Phi", "T.Phi"),
    "何張楊": ("Truong Duong", "T.Duong"),
    "馬張達": ("Truong Dat", "T.Dat"),
    "王張衛": ("Truong Ve", "T.Ve"),
    "張橫": ("Truong Hoanh", "T.Hoanh"),
    "張燕": ("Truong Yen", "T.Yen"),
    "張遼": ("Truong Lieu", "T.Lieu"),
    "張繡": ("Truong Tu", "T.Tu"),
    "張邈": ("Truong Mac", "T.Mac"),
    "張紘": ("Truong Hoanh", "T.Hoanh"),
    "張嶷": ("Truong Nghi", "T.Nghi"),
    "張闓": ("Truong Khai", "U.Khai"),
    "張肅": ("Truong Tuc", "T.Tuc"),
    "張紹": ("Truong Thieu", "T.Thieu"),
    "何張球": ("Truong Cau", "T.Cau"),
    "馬張約": ("Truong Uoc", "T.Uoc"),
    "王張緝": ("Truong Tap", "T.Tap"),
    "張節": ("Truong Tiet", "T.Tiet"),
    "張華": ("Truong Hoa", "T.Hoa"),
    "張悌": ("Truong De", "T.De"),
    "曹休": ("Tao Huu", "T.Huu"),
    "曹宇": ("Tao Vu", "T.Vu"),
    "曹安民": ("Tao An Dan", "T.An Dan"),
    "曹性": ("Tao Tinh", "T.Tinh"),
    "曹昂": ("Tao Ngoang", "T.Ngoang"),
    "曹洪": ("Tao Hong", "T.Hong"),
    "曹真": ("Tao Chan", "T.Chan"),
    "何曹訓": ("Tao Ton", "T.Ton"),
    "馬曹爽": ("Tao Suong", "T.Suong"),
    "王曹植": ("Tao Thuc", "T.Thuc"),
    "曹髦": ("Tao Mao", "T.Mao"),
    "曹操": ("Tao Thao", "Tao T"),
    "曹羲": ("Tao Hi", "T.Hi"),
    "曹遵": ("Tao Ton", "T.Ton"),
    "梁剛": ("Luong Cuong", "L.Cuong"),
    "梁寬": ("Luong Khoan", "L.Khoan"),
}

SURNAMES: dict[str, str] = {
    "劉": "Luu",
    "關": "Quan",
    "張": "Truong",
    "曹": "Tao",
    "孫": "Ton",
    "諸葛": "Gia Cat",
    "司馬": "Tu Ma",
    "夏侯": "Ha Hau",
    "馬": "Ma",
    "呂": "Lu",
    "袁": "Vien",
    "董": "Dong",
    "何": "Ha",
    "王": "Vuong",
    "趙": "Trieu",
    "黃": "Hoang",
    "許": "Xu",
    "陳": "Tran",
    "郭": "Quach",
    "陸": "Luc",
    "程": "Trinh",
    "費": "Phi",
    "馮": "Phung",
    "楊": "Duong",
    "賈": "Gia",
    "雍": "Ung",
    "葛": "Cat",
    "廖": "Lieu",
    "蔣": "Tuong",
    "蔡": "Thai",
    "鄭": "Trinh",
    "鄧": "Dang",
    "閻": "Dien",
    "霍": "Hoac",
    "駱": "Lac",
    "鮑": "Bao",
    "盧": "Lo",
    "鍾": "Chung",
    "應": "Ung",
    "韓": "Han",
    "顏": "Nhan",
    "龐": "Bang",
    "嚴": "Nghiem",
    "蘇": "To",
    "淳于": "Thuan Vu",
    "公孫": "Cong Ton",
    "毋丘": "Vo Khu",
    "太史": "Thai Su",
    "姜": "Khuong",
    "典": "Dien",
    "周": "Chu",
    "孟": "Man",
    "金": "Kim",
    "宗": "Tong",
    "封": "Phong",
    "侯": "Hau",
    "胡": "Ho",
    "紀": "Ky",
    "夏": "Ha",
    "徐": "Tu",
    "桓": "Hoan",
    "祖": "To",
    "秦": "Tan",
    "荀": "Tuan",
    "郝": "Hac",
    "高": "Cao",
    "崔": "Thoi",
    "梁": "Luong",
    "李": "Ly",
    "杜": "Do",
    "沈": "Tham",
    "辛": "Tan",
    "卑": "Ti",
    "和": "Hoa",
    "沮": "Tu",
    "卞": "Bien",
    "文": "Van",
    "甘": "Cam",
    "田": "Dien",
    "伍": "Ngu",
    "任": "Nham",
    "全": "Toan",
    "向": "Huong",
    "成": "Thanh",
    "朱": "Chu",
    "羊": "Duong",
    "汪": "Vuong",
    "冷": "Lanh",
    "吳": "Ngo",
    "岑": "Sam",
    "車": "Xa",
    "摩": "Ma",
    "史": "Su",
    "尹": "Doan",
    "左": "Ta",
    "石": "Thach",
    "丘": "Khu",
    "伊": "Y",
    "毛": "Mao",
    "孔": "Khong",
    "方": "Phuong",
    "范": "Pham",
    "韋": "Vi",
    "柳": "Lieu",
    "耿": "Cam",
    "羌": "Cuong",
    "師": "Su",
    "烏桓": "O Hoan",
    "宴": "Yen",
    "狗": "Cau",
    "膳": "Thien",
    "盒": "Hop",
    "烏": "O",
    "威": "Uy",
    "寶": "Bao",
    "覽": "Lam",
    "閉": "Bich",
    "抔": "Phau",
    "魴": "Phuong",
    "倉": "Thuong",
    "善": "Thien",
    "瑜": "Du",
    "昕": "Tan",
    "爬": "Ba",
    "爸": "Ba",
    "嬤": "Ma",
    "鶗": "De",
    "韙": "Vi",
    "炊": "Thuy",
    "壑": "Hac",
    "礞": "Man",
    "悀": "Dung",
    "公": "Cong",
    "于": "Vu",
    "丁": "Dinh",
    "子": "Tu",
    "華": "Hoa",
    "傅": "Pho",
    "牽": "Kham",
    "焦": "Tieu",
    "洞": "Dong",
    "逢": "Phung",
    "陰": "Am",
    "韓": "Han",
}

GIVEN: dict[str, str] = {
    "備": "Bi",
    "羽": "Vu",
    "飛": "Phi",
    "操": "Thao",
    "權": "Quyen",
    "亮": "Luong",
    "瑜": "Du",
    "布": "Bo",
    "雲": "Van",
    "超": "Sieu",
    "惇": "Don",
    "淵": "Vien",
    "維": "Duy",
    "懿": "Y",
    "朗": "Lang",
    "師": "Su",
    "昭": "Chieu",
    "炎": "Viem",
    "孚": "Phu",
    "望": "Vong",
    "攸": "Du",
    "佃": "Dien",
    "策": "Sach",
    "皓": "Hao",
    "乾": "Can",
    "桓": "Hoan",
    "朗": "Lang",
    "秀": "Tu",
    "仲": "Trung",
    "匡": "Khoang",
    "琳": "Lam",
    "歆": "Ham",
    "皎": "Kieu",
    "翊": "At",
    "觀": "Quan",
    "冀": "Ky",
    "韶": "Thieu",
    "瑜": "Nhu",
    "寧": "Ninh",
    "庶": "Thuc",
    "盛": "Thinh",
    "商": "Thuong",
    "茂": "Mao",
    "弼": "Tat",
    "宓": "Mat",
    "明": "Minh",
    "尚": "Thuong",
    "術": "Thuat",
    "熙": "Hy",
    "譚": "Dam",
    "遺": "Di",
    "岱": "Dai",
    "延": "Diem",
    "玩": "Hoan",
    "漢": "Han",
    "遵": "Ton",
    "謖": "Tuc",
    "元義": "Nguyen Nghia",
    "邈": "Dieu",
    "定": "Dinh",
    "順": "Thuan",
    "幹": "Can",
    "覽": "Lam",
    "昇": "Thang",
    "纂": "Toan",
    "琰": "Nghiem",
    "諒": "Luong",
    "角": "Giac",
    "讓": "Nhuong",
    "武": "Vu",
    "允": "Doan",
    "先": "Tien",
    "承": "Thua",
    "松": "Tong",
    "虎": "Ho",
    "南": "Nam",
    "郃": "Hach",
    "楊": "Duong",
    "達": "Dat",
    "衛": "Ve",
    "橫": "Hoanh",
    "燕": "Yen",
    "遼": "Lieu",
    "繡": "Tu",
    "紘": "Hoanh",
    "嶷": "Nghi",
    "闓": "Khai",
    "肅": "Tuc",
    "紹": "Thieu",
    "球": "Cau",
    "約": "Uoc",
    "緝": "Tap",
    "節": "Tiet",
    "華": "Hoa",
    "悌": "De",
    "休": "Huu",
    "宇": "Vu",
    "安民": "An Dan",
    "性": "Tinh",
    "昂": "Ngoang",
    "洪": "Hong",
    "真": "Chan",
    "訓": "Ton",
    "爽": "Suong",
    "植": "Thuc",
    "髦": "Mao",
    "羲": "Hi",
    "遵": "Ton",
    "剛": "Cuong",
    "寬": "Khoan",
}


def fit_abbrev(text: str, ascii_max: int) -> str:
    """Return ASCII-only abbrev with len <= ascii_max."""
    cleaned = ASCII_RE.sub("", text).strip()
    if not cleaned:
        return "UNK"[:ascii_max]
    if len(cleaned) <= ascii_max:
        return cleaned

    # Try dropping spaces first.
    nospace = cleaned.replace(" ", "")
    if len(nospace) <= ascii_max:
        return nospace

    # Two-token names: "Lu Chi" -> "L.Chi" or "LChi"
    words = cleaned.split()
    if len(words) == 2:
        a, b = words
        for candidate in (
            f"{a[0]}{b}",
            f"{a[0]}.{b}",
            f"{a[:2]}{b[0]}",
            f"{a[:2]}.{b[0]}",
            f"{a[0]}.{b[:ascii_max - 2]}",
        ):
            if 0 < len(candidate) <= ascii_max:
                return candidate

    if len(words) > 1:
        dotted = ".".join(w[0] for w in words if w)
        rest = words[-1]
        candidate = f"{dotted}.{rest}"
        if len(candidate) <= ascii_max:
            return candidate
        candidate = f"{words[0][0]}.{rest}"
        if len(candidate) <= ascii_max:
            return candidate
        # initials only
        if len(dotted) <= ascii_max:
            return dotted

    return nospace[:ascii_max]


def is_garbled(original: str) -> bool:
    if any(c in GARBLED_CHARS for c in original):
        return True
    # Residual weapon-prefix corruption with junk middle chars
    if re.search(r"[釭鞭龍斧蒺戟矛脊門].*[吨悀悜]", original):
        return True
    return False


def strip_prefixes(original: str) -> str:
    text = original
    changed = True
    while changed:
        changed = False
        for prefix in WEAPON_PREFIXES:
            if text.startswith(prefix) and len(text) > len(prefix):
                text = text[len(prefix) :]
                changed = True
                break
        if not changed:
            for prefix in FACTION_PREFIXES:
                if text.startswith(prefix) and len(text) > len(prefix):
                    # Don't strip if prefix is the actual surname (single char remainder check)
                    rest = text[len(prefix) :]
                    if len(rest) >= 2:
                        text = rest
                        changed = True
                        break
    return text


def make_abbrev_from_translated(translated: str, ascii_max: int) -> str:
    if translated == "[loi extract]":
        return fit_abbrev("UNK", ascii_max)
    return fit_abbrev(translated, ascii_max)


def split_name(original: str) -> tuple[str, str] | None:
    for sur, sur_vn in sorted(SURNAMES.items(), key=lambda x: -len(x[0])):
        if original.startswith(sur):
            given = original[len(sur) :]
            if given:
                return sur_vn, given
    return None


def translate_given(given: str) -> str:
    if given in GIVEN:
        return GIVEN[given]
    # Multi-char given names: try longest match chunks
    parts: list[str] = []
    i = 0
    while i < len(given):
        matched = False
        for length in range(min(3, len(given) - i), 0, -1):
            chunk = given[i : i + length]
            if chunk in GIVEN:
                parts.append(GIVEN[chunk])
                i += length
                matched = True
                break
        if not matched:
            parts.append(given[i])
            i += 1
    return " ".join(parts)


def translate_fallback(original: str) -> tuple[str, str]:
    if is_garbled(original):
        return "[loi extract]", "UNK"

    stripped = strip_prefixes(original)
    if stripped in EXACT:
        t, a = EXACT[stripped]
        return t, a

    if stripped != original and not is_garbled(stripped):
        split = split_name(stripped)
        if split:
            sur_vn, given = split
            given_vn = translate_given(given)
            translated = f"{sur_vn} {given_vn}".strip()
            abbrev = make_abbrev_from_translated(translated, 99)
            return translated, abbrev

    split = split_name(original)
    if split:
        sur_vn, given = split
        given_vn = translate_given(given)
        translated = f"{sur_vn} {given_vn}".strip()
        abbrev = make_abbrev_from_translated(translated, 99)
        return translated, abbrev

    return "[loi extract]", "UNK"


def translate_entry(original: str, ascii_max: int) -> tuple[str, str]:
    if original in EXACT:
        translated, abbrev_hint = EXACT[original]
    else:
        translated, abbrev_hint = translate_fallback(original)

    abbrev = fit_abbrev(abbrev_hint, ascii_max)
    if translated != "[loi extract]":
        # Prefer abbrev derived from hint; if too long, also try from translated
        if len(abbrev) > ascii_max:
            abbrev = fit_abbrev(translated, ascii_max)
    return translated, abbrev


def validate_entry(entry: dict) -> list[str]:
    errors: list[str] = []
    abbrev = entry.get("abbrev", "")
    ascii_max = entry.get("ascii_max", 0)
    if entry.get("status") != "done":
        errors.append("status not done")
    if not abbrev:
        errors.append("empty abbrev")
    if len(abbrev) > ascii_max:
        errors.append(f"abbrev too long: {len(abbrev)} > {ascii_max}")
    if ASCII_RE.search(abbrev):
        errors.append(f"non-ASCII in abbrev: {abbrev!r}")
    if not entry.get("translated"):
        errors.append("empty translated")
    return errors


def apply_translations(dry_run: bool = False) -> dict:
    with NAME_JSON.open(encoding="utf-8") as f:
        data = json.load(f)

    translated_count = 0
    errors: list[str] = []
    validation_errors: list[str] = []

    for idx in range(START_IDX, END_IDX + 1):
        entry = data[idx]
        if entry.get("status") == "done" and entry.get("translated"):
            continue

        original = entry["original"]
        ascii_max = entry["ascii_max"]
        translated, abbrev = translate_entry(original, ascii_max)

        entry["translated"] = translated
        entry["abbrev"] = abbrev
        entry["status"] = "done"
        translated_count += 1

        entry_errors = validate_entry(entry)
        if entry_errors:
            validation_errors.append(
                f"idx={idx} original={original!r}: {', '.join(entry_errors)}"
            )

    if EXACT:
        missing = []
        for idx in range(START_IDX, END_IDX + 1):
            orig = data[idx]["original"]
            if orig not in EXACT and translate_fallback(orig)[0] == "[loi extract]":
                missing.append((idx, orig))
        if missing:
            errors.append(f"unmapped entries: {len(missing)}")
            for idx, orig in missing[:10]:
                errors.append(f"  idx={idx}: {orig}")

    if not dry_run:
        with NAME_JSON.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")

    # Final validation pass on target range
    all_valid = True
    for idx in range(START_IDX, END_IDX + 1):
        ve = validate_entry(data[idx])
        if ve:
            all_valid = False
            validation_errors.append(
                f"post idx={idx} {data[idx]['original']!r}: {', '.join(ve)}"
            )

    return {
        "translated": translated_count,
        "range": f"{START_IDX}-{END_IDX}",
        "all_valid": all_valid,
        "errors": errors,
        "validation_errors": validation_errors,
    }


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    result = apply_translations(dry_run=dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["validation_errors"]:
        print("\nValidation failures:", file=sys.stderr)
        for e in result["validation_errors"]:
            print(e, file=sys.stderr)
        return 1
    if result["errors"]:
        print("\nWarnings:", file=sys.stderr)
        for e in result["errors"]:
            print(e, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
