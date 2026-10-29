# -*- coding: utf-8 -*-
"""Matnni odamdek o'qiladigan so'zlarga aylantirish (o'zbek tili).

"15:09" -> "o'n besh nol to'qqiz", "28.10.2026" -> "yigirma sakkizinchi oktabr ikki ming
yigirma olti yil", "25%" -> "yigirma besh foiz", "USB" -> "yu es bi", "@" -> "at" ...

Faqat standart Python kerak. Har qanday ovoz dvigateli oldidan ishlatiladi.
"""
import re

ONES = ["nol", "bir", "ikki", "uch", "to'rt", "besh", "olti", "yetti", "sakkiz", "to'qqiz"]
TENS = ["", "o'n", "yigirma", "o'ttiz", "qirq", "ellik", "oltmish", "yetmish", "sakson", "to'qson"]
BIG = [(10 ** 12, "trillion"), (10 ** 9, "milliard"), (10 ** 6, "million"), (1000, "ming")]

MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust",
          "sentabr", "oktabr", "noyabr", "dekabr"]

LETTERS = {
    "a": "a", "b": "be", "c": "se", "d": "de", "e": "e", "f": "ef", "g": "ge", "h": "ha",
    "i": "i", "j": "je", "k": "ka", "l": "el", "m": "em", "n": "en", "o": "o", "p": "pe",
    "q": "qa", "r": "er", "s": "es", "t": "te", "u": "u", "v": "ve", "w": "dubl ve",
    "x": "xa", "y": "ye", "z": "ze",
}

UNITS = {
    "km": "kilometr", "m": "metr", "sm": "santimetr", "mm": "millimetr", "kg": "kilogramm",
    "g": "gramm", "t": "tonna", "l": "litr", "ml": "millilitr", "gb": "gigabayt",
    "mb": "megabayt", "kb": "kilobayt", "tb": "terabayt", "mgs": "megagerts",
    "kvt": "kilovatt", "vt": "vatt", "gts": "gigagerts", "mah": "milliamper soat",
    "mln": "million", "mlrd": "milliard",
}

CURRENCY = {"$": "dollar", "€": "yevro", "₽": "rubl", "£": "funt", "₩": "von", "¥": "iyena"}

BRANDS = {
    "wi-fi": "vay fay", "wifi": "vay fay", "youtube": "yutub", "google": "gugl",
    "whatsapp": "vatsap", "bluetooth": "blutuz", "instagram": "instagram",
    "facebook": "feysbuk", "telegram": "telegram", "tiktok": "tiktok", "ok": "okey",
    "android": "android", "iphone": "ayfon", "windows": "vindovs",
    "chatgpt": "chat ji pi ti", "gmail": "jimeyl", "email": "imeyl", "e-mail": "imeyl",
    "sms": "es em es", "gps": "ji pi es", "usb": "yu es bi", "tv": "te ve", "pdf": "pe de ef",
}

# Hammasi bosh harf bilan yozilsa ham so'z sifatida o'qiladigan nomlar
WORD_CAPS = {"JARVIS", "UZBEKISTON", "TOSHKENT", "OK", "OKEY", "ALI", "OLIM"}

SYMBOLS = {
    "+": " plyus ", "=": " teng ", "*": " ko'paytirish ", "×": " ko'paytirish ",
    "÷": " bo'lish ", "<": " kichik ", ">": " katta ", "@": " at ", "#": " panjara ",
    "&": " va ", "_": " pastki chiziq ", "~": " tilda ", "^": " daraja ", "|": " ",
    "\\": " teskari kosa chiziq ", "§": " paragraf ", "©": " mualliflik huquqi ",
    "№": " raqami ", "°": " daraja ",
}

ABBREV = [
    (r"\bva h\.?\s?k\.?", "va hokazo"), (r"\bmas\.", "masalan"), (r"\bq\.\s?q\.", "qarang"),
    (r"\bkv\.", "kvadrat"),
]


def number_words(n):
    n = int(n)
    if n < 10:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ((" " + ONES[n % 10]) if n % 10 else "")
    if n < 1000:
        head = ("" if n // 100 == 1 else ONES[n // 100] + " ") + "yuz"
        return head + ((" " + number_words(n % 100)) if n % 100 else "")
    for value, name in BIG:
        if n >= value:
            high, rest = divmod(n, value)
            head = ("bir " if high == 1 and value == 1000 else number_words(high) + " ") + name
            return head + ((" " + number_words(rest)) if rest else "")
    return str(n)


def ordinal_words(n):
    words = number_words(n)
    last = words.split()[-1]
    return words + ("nchi" if last[-1] in "aeiou" else "inchi")


def digits_words(s):
    return " ".join(ONES[int(d)] for d in s if d.isdigit())


def decimal_words(whole, frac):
    k = len(frac)
    if k > 3:
        return number_words(int(whole)) + " butun " + digits_words(frac)
    denominators = {1: "o'ndan", 2: "yuzdan", 3: "mingdan"}
    return number_words(int(whole)) + " butun " + denominators[k] + " " + number_words(int(frac))


def year_number(y):
    y = int(y)
    words = number_words(y)
    if 1000 <= y < 2000:
        words = words.replace("bir ming", "ming", 1)     # "ming to'qqiz yuz to'qson to'qqiz"
    return words


def year_words(y):
    return year_number(y) + " yil"


def time_words(h, m):
    out = number_words(int(h))
    m = int(m)
    if m:
        out += " " + (("nol " + ONES[m]) if m < 10 else number_words(m))
    return out


def spell(token):
    return " ".join(LETTERS.get(c.lower(), c) for c in token if c.isalpha())


def _date(d, mo, y):
    d, mo = int(d), int(mo)
    if 1 <= mo <= 12 and 1 <= d <= 31:
        return " %s %s %s " % (ordinal_words(d), MONTHS[mo - 1], year_words(y))
    return None


def normalize_text(text):
    t = str(text)
    for ch in "ʻʼ’‘`´":
        t = t.replace(ch, "'")
    t = t.replace("…", ". ").replace("—", ", ").replace("–", "-")

    # --- havolalar va elektron pochta ---
    t = re.sub(r"https?://", "", t)
    t = re.sub(r"www\.", "vi vi vi nuqta ", t)
    t = re.sub(r"([\w.-]+)@([\w-]+(?:\.[\w-]+)+)",
               lambda m: m.group(1).replace(".", " nuqta ") + " at " + m.group(2).replace(".", " nuqta "), t)
    t = re.sub(r"\b([a-zA-Z0-9-]+)\.(uz|com|ru|org|net|io|me)\b", r"\1 nuqta \2", t)

    # --- sana: 28.10.2026(-yil), 2026-10-28 ---
    t = re.sub(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})(?:\s?-?\s?yil\w*)?\b",
               lambda m: _date(m.group(1), m.group(2), m.group(3)) or m.group(0), t)
    t = re.sub(r"\b(\d{4})-(\d{2})-(\d{2})(?:\s?-?\s?yil\w*)?\b",
               lambda m: _date(m.group(3), m.group(2), m.group(1)) or m.group(0), t)

    # --- vaqt: 15:09 ---
    t = re.sub(r"\b([01]?\d|2[0-3]):([0-5]\d)\b(?:\s?(ga|da|dan|gacha|dagi)\b)?",
               lambda m: " " + time_words(m.group(1), m.group(2)) + (m.group(3) or "") + " ", t)

    # --- yil: 2026-yil, 1999-yilda ---
    t = re.sub(r"\b(\d{4})\s?-\s?(yil\w*)", lambda m: " " + year_number(m.group(1)) + " " + m.group(2) + " ", t)

    # --- manfiy son va ayirish ---
    t = re.sub(r"(\d)\s+-\s+(\d)", r"\1 minus \2", t)
    t = re.sub(r"(?<![\w])-(\d)", r"minus \1", t)

    # --- tartib sonlar: 28-oktabr, 3-sinf, 5-inchi ---
    t = re.sub(r"\b(\d+)-(?:inchi|nchi|chi|ichi)\b", lambda m: " " + ordinal_words(m.group(1)) + " ", t)
    t = re.sub(r"\b(\d{1,4})-(?=[a-zA-Z'])", lambda m: " " + ordinal_words(m.group(1)) + " ", t)

    # --- pul, foiz, daraja ---
    t = re.sub(r"([$€₽£₩¥])\s?(\d+(?:[ ,.]\d{3})*(?:[,.]\d+)?)",
               lambda m: " " + m.group(2) + " " + CURRENCY[m.group(1)] + " ", t)
    t = re.sub(r"(\d)\s?%", r"\1 foiz", t)
    t = re.sub(r"(\d)\s?°\s?c\b", r"\1 daraja", t, flags=re.I)
    t = re.sub(r"(\d)\s?°", r"\1 daraja", t)

    # --- birliklar (raqamdan keyin) ---
    def unit(m):
        key = m.group(2).lower()
        return m.group(1) + " " + UNITS[key] if key in UNITS else m.group(0)

    t = re.sub(r"(\d)\s?([a-zA-Z]{1,4})\b", unit, t)

    # --- oraliq: 2-3 ---
    t = re.sub(r"\b(\d+)-(\d+)\b",
               lambda m: " " + number_words(m.group(1)) + "dan " + number_words(m.group(2)) + "gacha ", t)

    # --- minglik ajratgichli sonlar: 125 000, 1,250,000 ---
    t = re.sub(r"\b\d{1,3}(?:[ ,.]\d{3})+\b(?![,.]\d)",
               lambda m: str(int(re.sub(r"[ ,.]", "", m.group(0)))), t)

    # --- o'nlik kasr: 3,5  0.25 ---
    t = re.sub(r"\b(\d+)[,.](\d+)\b", lambda m: " " + decimal_words(m.group(1), m.group(2)) + " ", t)

    # --- oddiy sonlar (qo'shimcha bilan: 15 ta -> o'n beshta) ---
    t = re.sub(r"\b(\d+)\s(ga|da|dan|gacha|ta|ni|ning)\b",
               lambda m: " " + number_words(m.group(1)) + m.group(2) + " ", t)
    t = re.sub(r"\d+", lambda m: " " + number_words(m.group(0)) + " ", t)

    # --- qisqartmalar, brendlar, harflar ---
    for pattern, repl in ABBREV:
        t = re.sub(pattern, repl, t, flags=re.I)

    def word(m):
        w = m.group(0)
        low = w.lower()
        if low in BRANDS:
            return BRANDS[low]
        base, _, tail = low.partition("'")
        if tail and base in BRANDS:
            return BRANDS[base] + tail
        if w.isupper() and 2 <= len(w) <= 5 and w not in WORD_CAPS:
            return spell(w)               # USB, TV -> harflab
        if len(w) == 1 and w.isupper():
            return spell(w)               # alohida bosh harf: A -> a, B -> be
        return w

    t = re.sub(r"[A-Za-z][A-Za-z'-]*[A-Za-z]|[A-Za-z]", word, t)

    # --- belgilar va tinish ---
    for sym, spoken in SYMBOLS.items():
        t = t.replace(sym, spoken)
    t = t.replace("/", " kosa chiziq ").replace("%", " foiz ")
    t = re.sub(r"[\"“”«»()\[\]{}]", ", ", t)
    t = re.sub(r"[^\w\s'.,!?;:-]", " ", t, flags=re.UNICODE)
    t = re.sub(r"(?<=\s)-(?=\s)", ", ", t)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,.!?;:])", r"\1", t)
    t = re.sub(r"([,.;:]){2,}", r"\1", t)
    t = re.sub(r"([!?])[!?]+", r"\1", t)
    return t.strip()
