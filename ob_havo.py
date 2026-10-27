import json
import re
import urllib.parse
import urllib.request

# ob-havo Toshkent | Samarqandda ob-havo qanday | shaharim Toshkent
TRIGGERS = [r"re:\bob[\s-]?havo\b|\bhavo qanday\b|\bhavo harorati\b|\bshaharim\b"]

CODES = {
    0: "ochiq osmon", 1: "asosan ochiq", 2: "qisman bulutli", 3: "bulutli",
    45: "tuman", 48: "qirovli tuman", 51: "yengil shamollatma yomg'ir",
    53: "shamollatma yomg'ir", 55: "kuchli shamollatma yomg'ir",
    61: "yengil yomg'ir", 63: "yomg'ir", 65: "kuchli yomg'ir",
    71: "yengil qor", 73: "qor", 75: "kuchli qor", 80: "jala",
    81: "kuchli jala", 82: "juda kuchli jala", 95: "momaqaldiroq"
}

FILLER = {
    "ob", "havo", "ob-havo", "obhavo", "qanday", "qalay", "harorati", "bugun",
    "hozir", "ayt", "ber", "menga", "iltimos", "jarvis", "da", "dagi", "ning",
    "qanaqa", "nima", "bo'ladi", "haqida"
}


def _settings_path():
    import os
    import selfupdate
    return os.path.join(selfupdate.data_dir(), "weather_city.json")


def _saved_city():
    try:
        with open(_settings_path(), "r", encoding="utf-8") as f:
            return json.load(f).get("city")
    except Exception:
        return None


def _save_city(city):
    with open(_settings_path(), "w", encoding="utf-8") as f:
        json.dump({"city": city}, f, ensure_ascii=False)


def _clean_city(norm):
    words = []

    for w in norm.replace("-", " ").split():
        base = re.sub(r"(da|dagi|ning|ga|ni)$", "", w) if len(w) > 5 else w

        if w in FILLER or base in FILLER:
            continue

        words.append(base)

    return " ".join(words).strip()


def _get(url):
    import netutil
    return json.loads(netutil.fetch(url, 12).decode("utf-8"))


def run(text, jarvis):
    norm = jarvis._normalize(text)

    if "shaharim" in norm:
        city = _clean_city(norm.replace("shaharim", ""))

        if not city:
            return "Shahar nomini ayting, masalan: shaharim Toshkent"

        _save_city(city)
        return "Yaxshi, shahringiz: " + city.title() + ". Endi «ob-havo» desangiz yetarli."

    city = _clean_city(norm) or _saved_city()

    if not city:
        return "Qaysi shahar? Masalan: ob-havo Toshkent (yoki bir marta «shaharim Toshkent» deng)."

    try:
        geo = _get(
            "https://geocoding-api.open-meteo.com/v1/search?count=1&language=en&name="
            + urllib.parse.quote(city)
        )
        place = (geo.get("results") or [None])[0]

        if not place:
            return "«" + city + "» shahrini topa olmadim."

        data = _get(
            "https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s"
            "&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m"
            "&daily=temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=1"
            % (place["latitude"], place["longitude"])
        )
        now = data["current"]
        day = data["daily"]
        state = CODES.get(now.get("weather_code"), "ob-havo ma'lumoti")

        return (
            "%s: hozir %d°, %s. Sezilishi %d°, shamol %d km/s. "
            "Bugun %d° dan %d° gacha."
            % (
                place["name"], round(now["temperature_2m"]), state,
                round(now["apparent_temperature"]), round(now["wind_speed_10m"]),
                round(day["temperature_2m_min"][0]), round(day["temperature_2m_max"][0])
            )
        )

    except Exception:
        return "Ob-havoni olib bo'lmadi. Internet borligini tekshiring."
