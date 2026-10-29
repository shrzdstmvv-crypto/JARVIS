# -*- coding: utf-8 -*-
"""Neyron (inson ovoziga o'xshash) o'zbekcha ovozni GitHub'da sinash.

Bu skript ilovaga TEGMAYDI. U faqat:
  1) Hugging Face'da o'zbekcha ovoz modellari borligini tekshiradi,
  2) topilgan modelda namunalar yaratadi (WAV): raqam, sana, belgi, harf, tinish belgilari bilan,
  3) model hajmi va tezligini log'ga yozadi.
Natija: ovoz_namunalar/ papkasi (GitHub Actions "Artifacts" ichida yuklab olinadi).
"""
import os
import re
import sys
import time

from matn import normalize_text

CANDIDATES = [
    ("facebook/mms-tts-uzb-script_cyrillic", "cyrillic"),
    ("facebook/mms-tts-uzb-script_latin", "latin"),
    ("facebook/mms-tts-uzb", "latin"),
]

PHRASES = [
    "Salom! Men Jarvisman. Sizga qanday yordam bera olaman?",
    "Hozir soat 15:09. Bugun 28.10.2026-yil. Harorat 25°C, namlik 60%.",
    "Xo'p, bajardim. Budilnik ertalab 6:20 ga qo'yildi.",
    "Narxi 125 000 so'm, og'irligi 3,5 kg. USB, SMS va Wi-Fi ham bor.",
    "A, B, C harflari. 2+3=5. Menga example@mail.uz ga yoz.",
    "Bugun ob-havo qanday bo'ladi? Quyoshli va issiq... Ajoyib!",
]


def clean(text):
    t = str(text).lower()
    for ch in "ʻʼ’‘`´":
        t = t.replace(ch, "'")
    return re.sub(r"\s+", " ", t).strip()


def latin_to_cyrillic(text):
    t = clean(text)
    out = []
    table = {
        "a": "а", "b": "б", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "ҳ",
        "i": "и", "j": "ж", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о",
        "p": "п", "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в",
        "x": "х", "y": "й", "z": "з", "'": "ъ", "c": "к", "w": "в",
    }
    for w in re.split(r"(\s+|[,.!?;:-])", t):
        if not w or not re.match(r"[a-z']", w):
            out.append(w)
            continue
        w = w.replace("o'", "Ў").replace("g'", "Ғ")
        w = w.replace("sh", "Ш").replace("ch", "Ч").replace("yo", "Ё").replace("yu", "Ю")
        w = w.replace("ya", "Я").replace("ye", "е").replace("ng", "нг")
        if w.startswith("e"):
            w = "э" + w[1:]
        res = "".join(table.get(c, c) for c in w)
        out.append(res.replace("Ў", "ў").replace("Ғ", "ғ").replace("Ш", "ш")
                   .replace("Ч", "ч").replace("Ё", "ё").replace("Ю", "ю").replace("Я", "я"))
    return "".join(out)


def main():
    out_dir = "ovoz_namunalar"
    os.makedirs(out_dir, exist_ok=True)
    report = []

    # Matn tayyorlash natijasini ham saqlaymiz (xatolarni ko'rish uchun)
    with open(os.path.join(out_dir, "matn_tayyorlash.txt"), "w", encoding="utf-8") as f:
        for p in PHRASES:
            f.write(p + "\n  -> " + normalize_text(p) + "\n")

    try:
        from huggingface_hub import list_models
        found = [m.id for m in list_models(search="tts-uzb", limit=30)]
        found += [m.id for m in list_models(search="uzbek tts", limit=30)]
        print("Hugging Face qidiruvi (o'zbekcha TTS):", sorted(set(found)))
    except Exception as error:
        print("Qidiruv ishlamadi:", repr(error)[:200])

    import torch
    from scipy.io import wavfile
    from transformers import AutoTokenizer, VitsModel

    done = 0
    for model_id, script in CANDIDATES:
        print("\n=== Model:", model_id, "===")
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = VitsModel.from_pretrained(model_id)
            model.eval()
        except Exception as error:
            msg = "%s: yuklab bo'lmadi (%s)" % (model_id, repr(error)[:160])
            print(msg)
            report.append(msg)
            continue

        params = sum(p.numel() for p in model.parameters())
        rate = model.config.sampling_rate
        print("parametrlar: %.1f mln, fp32 hajmi taxminan %.0f MB, chastota %d Hz"
              % (params / 1e6, params * 4 / 1e6, rate))
        try:
            print("alifbo (belgilar):", "".join(sorted(tokenizer.get_vocab().keys())))
        except Exception:
            pass

        for index, phrase in enumerate(PHRASES, 1):
            spoken = normalize_text(phrase)
            text = latin_to_cyrillic(spoken) if script == "cyrillic" else clean(spoken)
            print("matn:", text)
            started = time.time()
            try:
                with torch.no_grad():
                    wave = model(**tokenizer(text, return_tensors="pt")).waveform[0].numpy()
            except Exception as error:
                print("  sintez xatosi:", repr(error)[:200])
                continue
            took = time.time() - started
            seconds = len(wave) / float(rate)
            print("  ovoz %.1f s, sintez %.1f s (koeffitsiyent %.2f)" % (seconds, took, took / max(seconds, 0.01)))
            wavfile.write(os.path.join(out_dir, "%s_%d.wav" % (model_id.split("/")[-1], index)), rate, wave)

        report.append("%s: tayyor (%.1f mln parametr)" % (model_id, params / 1e6))
        done += 1

    with open(os.path.join(out_dir, "hisobot.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report) or "hech narsa topilmadi")

    print("\nHISOBOT:\n" + "\n".join(report))
    if done == 0:
        print("Hech bir model ishlamadi. Bu natijaning o'zi muhim: boshqa yo'l kerak.")


if __name__ == "__main__":
    sys.exit(main())
