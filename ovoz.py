# -*- coding: utf-8 -*-
"""JARVIS o'z ovozi: o'zbek lotin yozuvi uchun qoidaga asoslangan formant sintezatori
(numpy'siz, sof Python; telefonda ishlaydi).

Hech qanday tashqi dvigatel, model yoki internet kerak emas. Matn -> fonemalar
-> formant filtrlari -> WAV. Ovoz ataylab "elektron" (Jarvis kabi) chiqadi.
"""
import array
import math
import os
import random
import re
import tempfile
import threading
import time
import wave


FS = 16000
FRAME = 80                      # 5 ms

# ---------------- fonemalar ----------------
# unli: (F1, F2, F3, davomiylik ms)
VOWELS = {
    "a": (720, 1250, 2600, 105),
    "e": (520, 1850, 2500, 100),
    "i": (330, 2150, 2900, 85),
    "o": (590, 930, 2500, 105),
    "u": (340, 850, 2300, 95),
    "O": (450, 1000, 2400, 100),    # o'
}

NASAL = {"m": (250, 1050, 2400), "n": (260, 1500, 2500), "N": (260, 2000, 2600)}   # N = ng
APPROX = {
    "l": (360, 1250, 2650, 70),
    "v": (300, 1000, 2200, 60),
    "y": (290, 2250, 3000, 60),
    "r": (420, 1350, 2400, 55),
}
# sirg'aluvchilar: (markaz, kenglik, shovqin kuchi, ovozlilik, davomiylik)
FRIC = {
    "s": (6200, 2800, 0.043, 0.0, 95),
    "z": (6200, 2800, 0.036, 0.35, 85),
    "S": (3200, 1900, 0.289, 0.0, 100),   # sh
    "f": (4500, 5000, 0.061, 0.0, 85),
    "x": (1800, 1700, 0.367, 0.0, 85),
    "h": (1500, 3000, 0.272, 0.0, 70),
    "G": (1200, 1100, 0.324, 0.40, 75),   # g'
}
# portlovchilar: (yopilish ms, portlash markazi, kengligi, kuchi, ovozli, aspiratsiya ms)
STOPS = {
    "p": (55, 900, 1400, 2.229, False, 18),
    "b": (45, 900, 1400, 1.175, True, 0),
    "t": (55, 4200, 2800, 0.221, False, 22),
    "d": (45, 4200, 2800, 0.187, True, 0),
    "k": (55, 2100, 1600, 0.586, False, 25),
    "g": (45, 2100, 1600, 0.567, True, 0),
    "q": (55, 1000, 900, 1.700, False, 22),
}
AFFR = {"C": (45, (3200, 1900, 0.289, 0.0, 85)),       # ch
        "J": (40, (3000, 1800, 0.231, 0.35, 70))}      # j


def seg(dur, f=(500, 1500, 2500), av=0.0, af=0.0, fc=3000, fbw=2000, vowel=False, stress=0.0,
        pause=None):
    return {"dur": dur, "f": f, "av": av, "af": af, "fc": fc, "fbw": fbw,
            "vowel": vowel, "stress": float(stress), "pause": pause}


# ---------------- matn -> fonemalar ----------------
ONES = ["nol", "bir", "ikki", "uch", "to'rt", "besh", "olti", "yetti", "sakkiz", "to'qqiz"]
TENS = ["", "o'n", "yigirma", "o'ttiz", "qirq", "ellik", "oltmish", "yetmish", "sakson", "to'qson"]


def number_words(n):
    if n < 10:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ((" " + ONES[n % 10]) if n % 10 else "")
    if n < 1000:
        head = ("" if n // 100 == 1 else ONES[n // 100] + " ") + "yuz"
        return head + ((" " + number_words(n % 100)) if n % 100 else "")
    if n < 1000000:
        head = ("bir " if n // 1000 == 1 else number_words(n // 1000) + " ") + "ming"
        return head + ((" " + number_words(n % 1000)) if n % 1000 else "")
    return " ".join(ONES[int(d)] for d in str(n))


def normalize(text):
    try:
        from matn import normalize_text
        text = normalize_text(text)
    except Exception:
        pass
    t = str(text).lower()
    for ch in "ʻʼ’‘`´":
        t = t.replace(ch, "'")
    t = t.replace("%", " foiz ").replace("+", " qo'sh ").replace("=", " teng ")
    t = re.sub(r"(\d+)[:.](\d+)", lambda m: m.group(1) + " , " + m.group(2), t)
    t = re.sub(r"\d+", lambda m: " " + number_words(int(m.group(0))) + " ", t)
    t = re.sub(r"[^a-z' ,.!?\n;:-]", " ", t)
    return t


def to_phones(word):
    """Bitta so'zni belgilar ro'yxatiga o'giradi (O=o', G=g', S=sh, C=ch, N=ng, J=j, '=tutuq)."""
    w = word.replace("o'", "O").replace("g'", "G")
    w = w.replace("sh", "S").replace("ch", "C").replace("ng", "N")
    w = w.replace("j", "J").replace("w", "v").replace("c", "s")
    out = []
    for ch in w:
        if ch == "'":
            out.append("'")
        elif ch in VOWELS or ch in NASAL or ch in APPROX or ch in FRAC_OR_STOP:
            out.append(ch)
    return out


FRAC_OR_STOP = set(FRIC) | set(STOPS) | set(AFFR)


def utterance(text):
    """-> segmentlar ro'yxati va har bir segment uchun to'xtam qiymatlari."""
    items = []          # ("word", [phones]) yoki ("pause", ms)
    for token in re.findall(r"[a-z']+|[,.!?;:\n-]", normalize(text)):
        if token in ",;:-":
            items.append(("pause", 170, ","))
        elif token == "?":
            items.append(("pause", 300, "?"))
        elif token in ".!\n":
            items.append(("pause", 300, "."))
        else:
            ph = to_phones(token)
            if ph:
                items.append(("word", ph))
    return items


def build_segments(items):
    segs = []
    prev_last = None            # oldingi so'zning oxirgi belgisi

    for pos, item in enumerate(items):
        if item[0] == "pause":
            segs.append(seg(item[1], pause=item[2]))
            prev_last = None
            continue

        phones = item[1]
        vowel_idx = [i for i, p in enumerate(phones) if p in VOWELS]
        stress_at = vowel_idx[-1] if vowel_idx else -1      # o'zbekchada urg'u odatda oxirgi unlida
        phrase_final = pos + 1 >= len(items) or items[pos + 1][0] == "pause"
        weight = 0.9 if phrase_final else 0.3

        # unli bilan tugagan so'zdan keyin unli bilan boshlangan so'z: ovoz uzilmasin
        if prev_last in VOWELS and phones and phones[0] in VOWELS:
            f1, f2, f3, _ = VOWELS[prev_last]
            segs.append(seg(22, (f1, f2, f3), av=0.35))

        for i, p in enumerate(phones):
            stressed = (i == stress_at)

            if p in VOWELS:
                f1, f2, f3, d = VOWELS[p]
                d = d * ((0.95 + 0.30 * weight) if stressed else 0.88)
                segs.append(seg(d, (f1, f2, f3), av=1.0, vowel=True,
                                stress=weight if stressed else 0.0))
            elif p in NASAL:
                segs.append(seg(70, NASAL[p], av=0.55))
            elif p in APPROX:
                f1, f2, f3, d = APPROX[p]
                if p == "r":
                    segs.append(seg(22, (f1, f2, f3), av=0.7))
                    segs.append(seg(14, (f1, f2, f3), av=0.12))
                    segs.append(seg(22, (f1, f2, f3), av=0.7))
                else:
                    segs.append(seg(d, (f1, f2, f3), av=0.7))
            elif p in FRIC:
                fc, bw, af, av, d = FRIC[p]
                segs.append(seg(d, (500, 1500, 2500), av=av, af=af, fc=fc, fbw=bw))
            elif p in STOPS:
                clo, fc, bw, af, voiced, asp = STOPS[p]
                segs.append(seg(clo, (250, 1200, 2300), av=0.14 if voiced else 0.0))
                segs.append(seg(9, (500, 1500, 2500), av=0.3 if voiced else 0.0, af=af, fc=fc, fbw=bw))
                if asp:
                    segs.append(seg(asp, (500, 1500, 2500), af=0.19, fc=1700, fbw=2200))
            elif p in AFFR:
                clo, (fc, bw, af, av, d) = AFFR[p]
                segs.append(seg(clo, (250, 1200, 2300), av=0.14 if av else 0.0))
                segs.append(seg(d, (500, 1500, 2500), av=av, af=af, fc=fc, fbw=bw))
            elif p == "'":
                segs.append(seg(45, (500, 1500, 2500)))

        prev_last = phones[-1] if phones else None
    return segs


# ---------------- sintez (sof Python) ----------------
def _coef(f, bw):
    r = math.exp(-math.pi * bw / FS)
    c = -r * r
    b = 2.0 * r * math.cos(2.0 * math.pi * f / FS)
    return 1.0 - b - c, b, c


def _smooth(values, k):
    if k <= 1 or not values:
        return list(values)
    pad = k // 2
    ext = [values[0]] * pad + list(values) + [values[-1]] * pad
    out, run = [], sum(ext[:k])
    out.append(run / k)
    for i in range(k, len(ext)):
        run += ext[i] - ext[i - k]
        out.append(run / k)
    return out[: len(values)]


def _close_phrase(store, length, kind):
    for k in range(length):
        store.append((k / float(max(1, length - 1)), kind))


def _contour(t, kind):
    """Jumla ichidagi ohang: asta pasayish + oxirida turga qarab tushish/ko'tarilish."""
    f = 1.04 - 0.10 * t
    tail = max(0.0, (t - 0.7) / 0.3)
    if kind == ".":
        f *= 1.0 - 0.17 * tail ** 1.5
    elif kind == "?":
        f *= 1.0 + 0.28 * max(0.0, (t - 0.65) / 0.35) ** 2
    elif kind == ",":
        f *= 1.0 + 0.06 * tail
    return f


def synthesize(text, base_f0=105.0, speed=1.0):
    """Matnni 16 kHz, 16 bitli (array('h')) ovozga aylantiradi."""
    segs = build_segments(utterance(text))
    if not segs:
        return array.array("h", [0] * (FS // 10))

    frames = []
    phrase_pos = []             # har kadr uchun jumla ichidagi o'rni (0..1) va jumla oxiri turi
    start = 0
    for s in segs:
        count = max(1, int(round(s["dur"] / speed / 5.0)))
        frames += [s] * count
        if s["pause"] is not None:
            _close_phrase(phrase_pos, len(frames) - count - start, s["pause"])
            phrase_pos += [(0.0, None)] * count
            start = len(frames)
    _close_phrase(phrase_pos, len(frames) - start, ".")
    nf = len(frames)

    F1 = _smooth([f["f"][0] for f in frames], 9)
    F2 = _smooth([f["f"][1] for f in frames], 9)
    F3 = _smooth([f["f"][2] for f in frames], 9)
    AV = _smooth([f["av"] for f in frames], 3)
    AF = _smooth([f["af"] for f in frames], 2)
    FC = [f["fc"] for f in frames]
    FB = [f["fbw"] for f in frames]
    ST = _smooth([f["stress"] for f in frames], 9)

    fixed = [_coef(3500, 260), _coef(4500, 300)]
    (a4, b4, c4), (a5, b5, c5) = fixed

    rnd = random.random
    out = [0.0] * (nf * FRAME)
    s1 = s2 = s3 = s4 = s5 = 0.0          # unli filtrlari: o'tgan chiqishlar
    t1 = t2 = t3 = t4 = t5 = 0.0          # ... va undan oldingilari
    n1 = n2 = 0.0                          # shovqin filtri holati
    phase = 0.0
    gprev = 0.0
    sin = math.sin
    inv_fs = 1.0 / FS

    for i in range(nf):
        t, kind = phrase_pos[i]
        f0 = base_f0 * _contour(t, kind) * (1 + 0.10 * ST[i]) * (1 + 0.012 * (rnd() - 0.5)) \
            * (1 + 0.004 * sin(i * 0.9))
        step = f0 * inv_fs
        av = AV[i] * (1.0 + 0.06 * (rnd() - 0.5))
        af = AF[i]
        base = i * FRAME

        voiced = av > 0.02
        if voiced:
            a1, b1, c1 = _coef(F1[i], 80)
            a2, b2, c2 = _coef(F2[i], 110)
            a3, b3, c3 = _coef(F3[i], 160)
        else:
            s1 = s2 = s3 = s4 = s5 = t1 = t2 = t3 = t4 = t5 = 0.0

        noisy = af > 0.001
        if noisy:
            ga, gb, gc = _coef(min(FC[i], 7600.0), max(300.0, FB[i] * 0.55))
            gain = (1.0 + FC[i] / 1500.0) * 1.3 * af
        else:
            n1 = n2 = 0.0

        for k in range(FRAME):
            phase += step
            if phase >= 1.0:
                phase -= 1.0
            if phase < 0.40:
                g = 0.5 * (1.0 - math.cos(3.141592653589793 * phase / 0.40))
            elif phase < 0.55:
                g = math.cos(3.141592653589793 * (phase - 0.40) / 0.30)
            else:
                g = 0.0
            d = g - gprev
            gprev = g

            y = 0.0
            if voiced:
                x = d * 40.0 * av + (rnd() * 2.0 - 1.0) * 0.866 * 0.05 * av
                v1 = a1 * x + b1 * s1 + c1 * t1
                t1 = s1
                s1 = v1
                v2 = a2 * v1 + b2 * s2 + c2 * t2
                t2 = s2
                s2 = v2
                v3 = a3 * v2 + b3 * s3 + c3 * t3
                t3 = s3
                s3 = v3
                v4 = a4 * v3 + b4 * s4 + c4 * t4
                t4 = s4
                s4 = v4
                v5 = a5 * v4 + b5 * s5 + c5 * t5
                t5 = s5
                s5 = v5
                y = v5

            if noisy:
                z = ga * (rnd() * 2.0 - 1.0) * 0.866 + gb * n1 + gc * n2
                n2 = n1
                n1 = z
                y += z * gain

            out[base + k] = y

    peak = max(max(out), -min(out)) or 1.0
    scale = 0.85 * 32767.0 / peak
    fade = int(0.01 * FS)
    n = len(out)
    for i in range(fade):
        w = i / float(fade)
        out[i] *= w
        out[n - 1 - i] *= w

    return array.array("h", [int(v * scale) for v in out])


def save_wav(path, samples):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(FS)
        w.writeframes(samples.tobytes() if hasattr(samples, "tobytes") else bytes(samples))


# ---------------- ijro (Android) ----------------
def _sentences(text, limit=170):
    parts, current = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+", text.strip()):
        if not sentence:
            continue
        if current and len(current) + len(sentence) + 1 > limit:
            parts.append(current)
            current = ""
        while len(sentence) > limit:
            cut = sentence.rfind(" ", 0, limit)
            cut = cut if cut > 20 else limit
            parts.append(sentence[:cut])
            sentence = sentence[cut:].strip()
        current = (current + " " + sentence).strip()
    if current:
        parts.append(current)
    return parts


class OwnVoice:
    """Matnni o'z ovozimiz bilan gapirtiradi (fonda, to'xtatib bo'ladi)."""

    def __init__(self):
        self.error = None
        self.generation = 0
        self.player = None
        self.lock = threading.Lock()
        base = os.environ.get("TMPDIR") or tempfile.gettempdir()
        self.paths = [os.path.join(base, "jarvis_ovoz_%d.wav" % i) for i in (0, 1)]

    def speak(self, text):
        self.stop()
        self.error = None
        generation = self.generation
        thread = threading.Thread(target=self._run, args=(text, generation), daemon=True)
        thread.start()
        return True

    def stop(self):
        self.generation += 1
        self._stop_player()

    def _stop_player(self):
        with self.lock:
            player, self.player = self.player, None
        if player is not None:
            try:
                player.stop()
            except Exception:
                pass
            try:
                player.release()
            except Exception:
                pass

    def _play(self, path):
        from jnius import autoclass

        player = autoclass("android.media.MediaPlayer")()
        player.setDataSource(path)
        player.prepare()
        player.start()
        with self.lock:
            self.player = player
        return player

    def _wait(self, player, generation):
        while generation == self.generation:
            try:
                if not player.isPlaying():
                    break
            except Exception:
                break
            time.sleep(0.05)

    def _run(self, text, generation):
        try:
            chunks = _sentences(text)
            if not chunks:
                return

            ready = synthesize(chunks[0])
            for index in range(len(chunks)):
                if generation != self.generation:
                    return

                path = self.paths[index % 2]
                save_wav(path, ready)
                player = self._play(path)

                # oldingisi o'qilayotganda keyingi gapni tayyorlaymiz
                if index + 1 < len(chunks):
                    ready = synthesize(chunks[index + 1])

                self._wait(player, generation)
                if generation == self.generation:
                    self._stop_player()
        except Exception as error:
            self.error = "Jarvis ovozi ishlamadi: " + repr(error)[:120]
            print("OVOZ ERROR:", error)
