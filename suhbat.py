import datetime
import random
import re

# Suhbat lug'ati: oddiy savol-javoblar, hazil, maqol, kayfiyat
TRIGGERS = [
    r"re:\brahmat\b|\btashakkur\b|\bkatta rahmat\b|\braxmat\b",
    r"re:\bismin\w* nima\b|\bkimsan\b|\bkimsiz\b|\bo'zingni tanishtir\b|\bkim bo'lasan\b",
    r"re:\bqalaysan\b|\bqalaysiz\b|\bahvol\w*\b|\bqanaqasan\b|\bkayfiyat\w* qanday\b|\bnima gap\b|\byaxshimisan\b|\byaxshimisiz\b",
    r"re:\bxayrli (?:tong|kun|kech|tun)\b|\bhayrli (?:tong|kun|kech|tun)\b|\bqayirli (?:tong|kun|kech|tun)\b",
    r"re:\blatifa\b|\bhazil\b|\bkuldir\b|\bqiziq gap\b",
    r"re:\bmaqol\b|\bhikmat\b|\bdonolik\b",
    r"re:\bcharchadim\b|\bzerikdim\b|\bxafaman\b|\bko'nglim\b|\bhafaman\b|\bqiynalyapman\b",
    r"re:\bbarakalla\b|\bofarin\b|\bzo'rsan\b|\byaxshi ishladin\b|\baqllisan\b|\bsevaman seni\b",
    r"re:\bkim yaratgan\b|\bseni kim yaratgan\b|\bkim yasagan\b|\bkim tuzgan\b",
    r"re:\bnima qilyapsan\b|\bnima qilyapsiz\b|\bnima qilasan\b",
    r"re:\btanga tashla\b|\btanga\b.*\btashla\b|\bkubik tashla\b|\bzar tashla\b",
    r"re:\b\d+\s*(?:dan|ta)\s*\d+\s*(?:gacha|ta)\b.*\bson\b|\btasodifiy son\b|\bson ayt\b",
]

JOKES = [
    "Dasturchi nega ko'zoynak taqadi? Chunki C# ni ko'ra olmaydi.",
    "O'qituvchi: «Bolalar, 5 ta olmadan 2 tasini olsam nechta qoladi?» Bola: «Siz olmagan 3 tasi, qolgani esa meniki.»",
    "Telefon zaryadi 1% bo'lganda, odam ham telefon ham o'zi uchun duo qiladi.",
    "Kompyuter doktorga boribdi: «Menda virus bor». Doktor: «Men sizga antivirus yozib beraman, lekin avval dam oling.»",
    "Do'stim: «Ertaga boshlayman». Men: «Ertaga ham shunday degan eding». U: «Ko'ryapsanmi, izchilman.»",
]

PROVERBS = [
    "Bir yigitga qirq hunar oz.",
    "Ilm olish — farz, amal qilish — qarz.",
    "Yaxshi so'z — jon ozig'i, yomon so'z — jon qozig'i.",
    "Ish bilan ishlagan — tinch yurar, ishsiz yurgan — ming muammo ko'rar.",
    "Sabr tagi — sariq oltin.",
    "Ko'p bilgan — ko'p yurar, ko'p yurgan — ko'p ko'rar.",
    "Oz-oz o'rganib dono bo'lur, qatra-qatra jam bo'lib daryo bo'lur.",
    "Birlashgan o'zar, birlashmagan to'zar.",
]

COMFORT = [
    "Tushunaman. Bir oz nafas oling, men shu yerdaman. Xohlasangiz, biror yoqimli narsa haqida gaplashamiz.",
    "Ba'zan shunday kunlar bo'ladi. Qisqa tanaffus qilib, bir stakan choy ichishni tavsiya qilaman.",
    "Siz o'ylagandan ham kuchliroqsiz. Kichik bir ishni bajaring, kayfiyat o'zi ko'tariladi.",
]


def _greeting_by_time():
    hour = datetime.datetime.now().hour

    if hour < 5:
        return "Xayrli tun"
    if hour < 11:
        return "Xayrli tong"
    if hour < 17:
        return "Xayrli kun"
    if hour < 22:
        return "Xayrli kech"

    return "Xayrli tun"


def _number_range(norm):
    match = re.search(r"(\d+)\s*(?:dan|ta)?\s*(\d+)\s*(?:gacha|ta)", norm)

    if match:
        a, b = sorted((int(match.group(1)), int(match.group(2))))
        return a, b

    return 1, 100


def run(text, jarvis):
    n = jarvis._normalize(text)

    if re.search(r"\b(rahmat|tashakkur|raxmat)\b", n):
        return random.choice(["Arzimaydi!", "Doim tayyorman.", "Marhamat, yana kerak bo'lsam ayting."])

    if re.search(r"\bkim yaratgan\b|\bkim yasagan\b|\bkim tuzgan\b", n):
        return "Meni egam o'z qo'li bilan yaratgan va men har kuni yangi narsalarni o'rganib boryapman."

    if re.search(r"ismin\w* nima|kimsan|kimsiz|tanishtir|kim bo'lasan", n):
        return "Men JARVIS, sizning shaxsiy yordamchingizman. Yangi narsalarni o'rganaman va telefoningiz bilan ishlashda yordam beraman."

    if re.search(r"xayrli|hayrli|qayirli", n):
        for part in ("tong", "kun", "kech", "tun"):
            if re.search(r"\b" + part + r"\b", n):
                return "Xayrli " + part + "!"

        return _greeting_by_time() + "!"

    if re.search(r"qalaysan|qalaysiz|ahvol|qanaqasan|kayfiyat|nima gap|yaxshimisan|yaxshimisiz", n):
        return random.choice([
            "Yaxshiman, rahmat! Siz-chi?",
            "Zo'rman, har doimgidek tayyorman. Sizda ahvollar qanday?",
            "Ajoyib! Nima yordam kerak?"
        ])

    if re.search(r"latifa|hazil|kuldir|qiziq gap", n):
        return random.choice(JOKES)

    if re.search(r"maqol|hikmat|donolik", n):
        return random.choice(PROVERBS)

    if re.search(r"charchadim|zerikdim|xafaman|hafaman|ko'nglim|qiynalyapman", n):
        return random.choice(COMFORT)

    if re.search(r"barakalla|ofarin|zo'rsan|aqllisan|yaxshi ishladin|sevaman", n):
        return random.choice(["Rahmat, bu menga kuch beradi!", "Sizdan eshitish juda yoqimli.", "Birga yaxshi jamoamiz!"])

    if re.search(r"nima qilyapsan|nima qilyapsiz|nima qilasan", n):
        return "Sizni kutib turibman va yangi narsalarni o'rganyapman. Biror buyruq bering."

    if re.search(r"tanga|gerb", n):
        return random.choice(["Gerb tushdi.", "Raqam tushdi."])

    if re.search(r"kubik|zar tashla", n):
        return "Zar: " + str(random.randint(1, 6))

    if re.search(r"tasodifiy son|son ayt|gacha", n):
        a, b = _number_range(n)
        return "Tasodifiy son (%d-%d): %d" % (a, b, random.randint(a, b))

    return None
