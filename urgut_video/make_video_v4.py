#!/usr/bin/env python3
"""Urgut Hills AI Dashboard — loyiha videosi, v4.

v3 dan farqi: sun'iy espeak-ng ovozi o'rniga tabiiy o'zbekcha neyron ovoz
(Microsoft edge-tts, uz-UZ-MadinaNeural). Har bir bo'lak alohida sintez qilinadi,
WordBoundary vaqt belgilari orqali ekrandagi so'zlar ovozga moslashtiriladi.

Ko'rinish dizayni v2/v3 videosidan o'lchab olingan (fon, shriftlar, ranglar,
joylashuv). Faqat ovoz, sinxronizatsiya va musiqa yangilangan.

Ishga tushirish:
    python3 make_video_v4.py --out /mnt/user-data/outputs/urgut-hills-loyiha-v4.mp4
"""
from __future__ import annotations

import argparse
import asyncio
import difflib
import json
import math
import os
import re
import shutil
import ssl
import subprocess
import sys
import wave
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent

# ----------------------------------------------------------------------------
# Sozlamalar
# ----------------------------------------------------------------------------
W, H, FPS = 1280, 720, 30
SR = 48000
VOICE = "uz-UZ-MadinaNeural"
VOICE_RATE = "-4%"          # biroz sekinroq, aniqroq talaffuz uchun

LEAD = 0.70                 # sahna boshidan birinchi bo'lakkacha (s)
GAP = 0.45                  # bo'laklar orasidagi pauza (s)
TAIL = 1.00                 # oxirgi bo'lakdan keyin sahna oxirigacha (s)
FADE = 0.35                 # sahna qora fondan chiqishi / kirishi (s)

FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Ranglar (v2 videodan o'lchangan)
BLUE = (59, 130, 246)
TITLE_C = (241, 245, 249)
TEXT_C = (241, 245, 249)
MUTED = (148, 163, 184)
GREEN = (34, 197, 94)
CARD_FILL = (20, 32, 56)
DIM_K = 0.28                # o'qilmagan so'z: asl rang bilan fonning aralashmasi

# ----------------------------------------------------------------------------
# SAHNALAR: (yorliq, sarlavha, tartib, [(rol, show, say), ...], qo'shimcha)
#   show — ekranda ko'rinadigan matn, say — ovozga beriladigan matn
# ----------------------------------------------------------------------------
SCENES = [
    ("", "", "cover", [
        ("big", "Urgut Hills AI Dashboard", "Urgut Hills A I dashbord."),
        ("sub", "Multi-agent biznes-intellekt platformasi", "Multi-agent biznes-intellekt platformasi."),
        ("note", "Loyihaning to'liq tavsifi", "Loyihaning to'liq tavsifi."),
    ]),
    ("MAQSAD", "Asosiy maqsad", "bullets", [
        ("bullet", "Ko'proq kvartira sotish", "Asosiy maqsad: ko'proq kvartira sotish,"),
        ("bullet", "Reklama xarajatini samarali sarflash", "reklama xarajatini samarali sarflash,"),
        ("bullet", "Jamoa samaradorligini oshirish", "jamoa samaradorligini oshirish."),
        ("bullet", "Har bir tavsiya dalil va tasdiq bilan", "Har bir tavsiya dalil va tasdiq bilan beriladi."),
    ]),
    ("RAQAMLAR", "Platforma raqamlarda", "cards", [
        ("card", "8|AI agent", "Platformada sakkizta A I agent,"),
        ("card", "4|rol bo'yicha dashboard", "to'rtta rol bo'yicha dashbord,"),
        ("card", "6|rivojlanish bosqichi", "olti rivojlanish bosqichi"),
        ("card", "2|integratsiya: amoCRM va Meta", "va ikkita integratsiya: amo CRM va Meta."),
    ]),
    ("JAMOA", "Jamoa tuzilmasi", "bullets", [
        ("bullet", "Producer: strategik nazorat", "Prodyuser: strategik nazorat."),
        ("bullet", "Project Manager: operatsiya va tasdiqlash", "Projekt menejer: operatsiya va tasdiqlash."),
        ("bullet", "ROP: sotuv bo'limi samaradorligi", "R O P: sotuv bo'limi samaradorligi."),
        ("bullet", "Sotuv menejerlari va call center operatorlari", "Sotuv menejerlari va koll senter operatorlari."),
        ("bullet", "Targetologist, videograf va montajchi", "Targetolog, videograf va montajchi."),
    ]),
    ("MA'LUMOT", "Ma'lumot manbalari", "flow", [
        ("box", "Meta Ads", "Ma'lumot manbalari: Meta Ads,"),
        ("box", "amoCRM", "amo CRM,"),
        ("box", "Qo'ng'iroq yozuvlari", "qo'ng'iroq yozuvlari"),
        ("box", "Sotuv rejalari", "va sotuv rejalari."),
        ("caption", "Hammasi yagona ma'lumot omboriga yig'iladi", "Hammasi yagona ma'lumot omboriga yig'iladi."),
    ]),
    ("JARAYON", "Ish oqimi (1/2)", "flow", [
        ("box", "Reklama lead yaratadi", "Reklama lid yaratadi,"),
        ("box", "Operator qo'ng'iroq qiladi", "operator qo'ng'iroq qiladi,"),
        ("box", "AI qo'ng'iroqni tahlil qiladi", "A I qo'ng'iroqni tahlil qiladi"),
        ("box", "Lead sifati baholanadi", "va lid sifati baholanadi."),
        ("caption", "Maqsad: 30 daqiqa ichida javob, ofisga taklif", "Maqsad: o'ttiz daqiqa ichida javob va ofisga taklif."),
    ]),
    ("JARAYON", "Ish oqimi (2/2)", "flow", [
        ("box", "Agentlar xabarlashadi", "Keyin agentlar xabarlashadi,"),
        ("box", "Tavsiya tayyorlanadi", "tavsiya tayyorlanadi,"),
        ("box", "Project Manager tasdiqlaydi", "projekt menejer tasdiqlaydi"),
        ("box", "Natija o'lchanadi", "va natija o'lchanadi."),
        ("caption", "Hech bir muhim qaror avtomatik bajarilmaydi", "Hech bir muhim qaror avtomatik bajarilmaydi."),
    ]),
    ("SIFAT", "Sifatli lead nima?", "bullets", [
        ("bullet", "Sifatli lead: ofisga kelgan va suhbatdan qoniqqan mijoz",
         "Sifatli lid: ofisga kelgan va suhbatdan qoniqqan mijoz."),
        ("bullet", "Narx bo'yicha norozi tugagan suhbat: yomon natija",
         "Narx bo'yicha norozi tugagan suhbat: yomon natija."),
        ("bullet", "Qo'ng'iroq tahlili: rozilik, kayfiyat, e'tiroz, ma'lumot sifati",
         "Qo'ng'iroq tahlili: rozilik, kayfiyat, e'tiroz, ma'lumot sifati."),
        ("bullet", "Natija reklama kampaniyasiga bog'lanadi", "Natija reklama kampaniyasiga bog'lanadi."),
    ]),
    ("AI AGENTLAR", "Multi-agent tizim", "bullets", [
        ("sub", "Har bir bo'lim o'z AI agentiga ega", "Har bir bo'lim o'z A I agentiga ega:"),
        ("bullet", "Targetolog AI, Call Center AI, Sales Manager AI",
         "Targetolog A I, koll senter A I, seyls menejer A I,"),
        ("bullet", "ROP AI, Videograf AI, Video Editor AI", "R O P A I, videograf A I, video editor A I,"),
        ("bullet", "Project Manager AI va Producer AI", "projekt menejer A I va prodyuser A I."),
        ("bullet", "Agentlar faqat dalilga asoslanib xulosa chiqaradi",
         "Agentlar faqat dalilga asoslanib xulosa chiqaradi."),
    ]),
    ("AI AGENTLAR", "Agentlar aloqasi (misol)", "flow", [
        ("box", "Call Center AI: narx e'tirozi", "Misol: koll senter A I narx e'tirozini aniqlaydi,"),
        ("box", "Targetolog AI: kampaniya B", "targetolog A I kampaniya B ni topadi,"),
        ("box", "Video agentlari: kreativ", "video agentlari kreativ tayyorlaydi,"),
        ("box", "Project Manager: vazifa", "projekt menejer vazifa beradi,"),
        ("box", "Producer: xulosa", "prodyuser esa xulosa qiladi."),
        ("caption", "Har bir xabar: manba, dalil, ishonch darajasi, muhimlik",
         "Har bir xabarda manba, dalil, ishonch darajasi va muhimlik bor."),
    ]),
    ("BOSHQARUV", "Tasdiqlash oqimi", "flow", [
        ("box", "Tavsiya", "Tasdiqlash oqimi: tavsiya,"),
        ("box", "PM tasdiqlaydi", "P M tasdiqlaydi,"),
        ("box", "Vazifa yaratiladi", "vazifa yaratiladi,"),
        ("box", "Bajarildi", "bajarildi"),
        ("box", "Natija o'lchanadi", "va natija o'lchanadi."),
        ("caption", "Zaxira tasdiqlovchi: Producer yoki ROP", "Zaxira tasdiqlovchi: prodyuser yoki R O P."),
    ]),
    ("ROLLAR", "Rollar va ruxsatlar", "bullets", [
        ("bullet", "Producer: umumiy ko'rinish, reklama xarajati", "Prodyuser: umumiy ko'rinish va reklama xarajati."),
        ("bullet", "Project Manager: barcha bo'limlar va tasdiqlash",
         "Projekt menejer: barcha bo'limlar va tasdiqlash."),
        ("bullet", "ROP: sotuv va call center ma'lumotlari", "R O P: sotuv va koll senter ma'lumotlari."),
        ("bullet", "Targetologist: reklama, mijoz telefoni yashirin",
         "Targetolog: reklama, mijoz telefoni yashirin."),
        ("bullet", "Operator: faqat o'z leadlari", "Operator: faqat o'z lidlari."),
    ]),
    ("PLATFORMA", "Dashboardlar", "bullets", [
        ("bullet", "Umumiy ko'rinish: KPI, voronka, kampaniyalar",
         "Dashbordlar: umumiy ko'rinish, K P I, voronka, kampaniyalar."),
        ("bullet", "Leadlar va qo'ng'iroqlar: tafsilot va coaching", "Lidlar va qo'ng'iroqlar: tafsilot va kouching."),
        ("bullet", "Reklama: xarajat va sifatli lead narxi", "Reklama: xarajat va sifatli lid narxi."),
        ("bullet", "Tavsiyalar: dalil, tasdiq va audit jurnali", "Tavsiyalar: dalil, tasdiq va audit jurnali."),
        ("bullet", "Agent xabarlari va sotuv rejasi", "Agent xabarlari va sotuv rejasi."),
    ]),
    ("PLATFORMA", "Texnik arxitektura", "arch", [
        ("box", "Next.js + TypeScript", "Texnik arxitektura: Nekst J S va Tayp Skript,"),
        ("box", "FastAPI (Python)", "Fast A P I, Payton,"),
        ("box", "PostgreSQL", "Postgres Q L."),
        ("caption", "Redis + Celery: fon ishlari", "Redis va Seleri: fon ishlari."),
        ("caption", "Model gateway: OpenAI, Anthropic, Gemini", "Model geytvey: Open A I, Entropik, Jemini."),
        ("caption", "Integratsiya: amoCRM API va Meta Marketing API",
         "Integratsiya: amo CRM A P I va Meta Marketing A P I."),
    ]),
    ("XAVFSIZLIK", "Xavfsizlik", "bullets", [
        ("bullet", "RBAC va PostgreSQL darajasida ruxsat (RLS)", "R B A C va Postgres Q L darajasida ruxsat, R L S."),
        ("bullet", "API kalitlari faqat serverda, vaultda saqlanadi",
         "A P I kalitlari faqat serverda, voltda saqlanadi."),
        ("bullet", "Mijoz ma'lumoti LLM'ga yuborilishdan oldin maskalanadi",
         "Mijoz ma'lumoti L L M ga yuborilishdan oldin maskalanadi."),
        ("bullet", "Audit jurnali: kim ko'rdi, kim tasdiqladi", "Audit jurnali: kim ko'rdi, kim tasdiqladi."),
        ("bullet", "Tokenlar chatda emas, xavfsiz kanal orqali", "Tokenlar chatda emas, xavfsiz kanal orqali uzatiladi."),
    ]),
    ("YO'L XARITASI", "Rivojlanish bosqichlari", "bullets", [
        ("bullet", "Faza 0: Discovery (KPI ta'riflari, audit, yuridik tekshiruv)",
         "Faza nol: diskaveri. K P I ta'riflari, audit, yuridik tekshiruv."),
        ("bullet", "Faza 1: Ma'lumot poydevori (amoCRM, Meta, attribution)",
         "Faza bir: ma'lumot poydevori. amo CRM, Meta, atribyushn."),
        ("bullet", "Faza 2: Qo'ng'iroqlar pipeline'i va AI baholash",
         "Faza ikki: qo'ng'iroqlar payplayni va A I baholash."),
        ("bullet", "Faza 3-4: AI tahlil va multi-agent aloqa", "Faza uch-to'rt: A I tahlil va multi-agent aloqa."),
        ("bullet", "Faza 5-6: Boshqaruv, tasdiqlash, optimallashtirish",
         "Faza besh-olti: boshqaruv, tasdiqlash, optimallashtirish."),
    ]),
    ("XAVFLAR", "Xavflar va ochiq savollar", "bullets", [
        ("bullet", "Attribution sifati: lead va reklamani to'g'ri bog'lash",
         "Atribyushn sifati: lid va reklamani to'g'ri bog'lash."),
        ("bullet", "O'zbek-rus aralash nutq uchun transkripsiya sifati",
         "O'zbek-rus aralash nutq uchun transkripsiya sifati."),
        ("bullet", "30 daqiqa qoidasi va ofis tashrifi ta'rifi", "O'ttiz daqiqa qoidasi va ofis tashrifi ta'rifi."),
        ("bullet", "Tarixiy ma'lumot muddati, byudjet va jamoa", "Tarixiy ma'lumot muddati, byudjet va jamoa."),
        ("bullet", "Meta Housing reklama cheklovlari", "Meta Hauzing reklama cheklovlari."),
    ]),
    ("", "", "cover", [
        ("big", "Urgut Hills AI Dashboard", "Urgut Hills A I dashbord."),
        ("sub", "Marketing → Lead → Qo'ng'iroq → Sotuv", "Marketing, lid, qo'ng'iroq, sotuv."),
        ("note", "AI: nima uchun, qayerda, kim va nima qilish kerak",
         "A I aytadi: nima uchun, qayerda, kim va nima qilish kerak."),
    ]),
]

# ----------------------------------------------------------------------------
# 1. TTS (edge-tts, WordBoundary)
# ----------------------------------------------------------------------------

def _ssl_ctx():
    for p in (os.environ.get("SSL_CERT_FILE"), "/root/.ccr/ca-bundle.crt"):
        if p and os.path.exists(p):
            return ssl.create_default_context(cafile=p)
    return None


async def _synth(text: str, mp3: Path) -> list[dict]:
    import edge_tts
    import edge_tts.communicate as ec
    ctx = _ssl_ctx()
    if ctx is not None:
        ec._SSL_CTX = ctx
    com = edge_tts.Communicate(text, VOICE, rate=VOICE_RATE, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({"text": ch["text"], "start": ch["offset"] / 1e7,
                              "end": (ch["offset"] + ch["duration"]) / 1e7})
    return words


def synth_chunk(text: str, cache: Path, idx: str) -> tuple[np.ndarray, list[dict]]:
    """Bo'lakni sintez qiladi -> (mono float32 @SR, so'z vaqtlari)."""
    mp3, js, wav = cache / f"{idx}.mp3", cache / f"{idx}.json", cache / f"{idx}.wav"
    meta = {"text": text, "voice": VOICE, "rate": VOICE_RATE}
    if not (js.exists() and wav.exists() and json.loads(js.read_text()).get("meta") == meta):
        for attempt in range(5):
            try:
                words = asyncio.run(_synth(text, mp3))
                if mp3.stat().st_size > 1000:
                    break
            except Exception as e:  # tarmoq xatosi — qayta urinish
                print(f"  TTS xato ({e}); qayta urinish {attempt + 1}", file=sys.stderr)
        else:
            raise RuntimeError(f"TTS ishlamadi: {text!r}")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-ac", "1", "-ar", str(SR),
                        "-c:a", "pcm_s16le", str(wav)], check=True)
        js.write_text(json.dumps({"meta": meta, "words": words}, ensure_ascii=False, indent=1))
    words = json.loads(js.read_text())["words"]
    with wave.open(str(wav)) as w:
        audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    # boshidagi / oxiridagi jimlikni qirqish (vaqt belgilarini ham surish)
    env = np.abs(audio) > 0.004
    nz = np.where(env)[0]
    a0 = max(0, nz[0] - int(0.03 * SR)) if len(nz) else 0
    a1 = min(len(audio), nz[-1] + int(0.08 * SR)) if len(nz) else len(audio)
    audio = audio[a0:a1]
    sh = a0 / SR
    for w_ in words:
        w_["start"] = max(0.0, w_["start"] - sh)
        w_["end"] = min(len(audio) / SR, w_["end"] - sh)
    return audio, words

# ----------------------------------------------------------------------------
# 2. Ekrandagi so'zlarni ovozdagi so'zlarga moslash
# ----------------------------------------------------------------------------
NUM = {"0": "nol", "1": "bir", "2": "ikki", "3": "uch", "4": "tort", "5": "besh", "6": "olti",
       "7": "yetti", "8": "sakkiz", "9": "toqqiz", "30": "ottiz", "18": "un sakkiz"}
# ekrandagi atamalar -> o'qilish shakli (normalizatsiya uchun)
SPOKEN = {"producer": "prodyuser", "project": "projekt", "manager": "menejer", "dashboard": "dashbord",
          "dashboardlar": "dashbordlar", "lead": "lid", "leadlar": "lidlar", "leadlari": "lidlari",
          "call": "koll", "center": "senter", "sales": "seyls", "targetologist": "targetolog",
          "coaching": "kouching", "discovery": "diskaveri", "attribution": "atribyushn",
          "pipelinei": "payplayni", "housing": "hauzing", "vaultda": "voltda", "python": "payton",
          "nextjs": "nekstjs", "typescript": "taypskript", "postgresql": "postgresql",
          "celery": "seleri", "gateway": "geytvey", "openai": "openai", "anthropic": "entropik",
          "gemini": "jemini", "llmga": "llmga"}


def norm(tok: str) -> str:
    t = tok.lower().replace("’", "'").replace("ʻ", "'").replace("ʼ", "'")
    parts = re.split(r"[-/]", t)
    out = []
    for p in parts:
        p2 = re.sub(r"[^0-9a-z]", "", p)
        if p2.isdigit():
            out.append(NUM.get(p2, p2).replace(" ", ""))
        else:
            out.append(SPOKEN.get(p2, p2))
    return "".join(out)


def sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def align(show_tokens: list[str], words: list[dict]) -> tuple[list[tuple[float, float]], float]:
    """Ekran so'zlari uchun (start, end) va moslik ulushini qaytaradi.

    Dinamik dasturlash: ekran so'zi 1..4 ta ketma-ket ovoz so'ziga mos kelishi mumkin
    ("ROP" <-> "R O P", "amoCRM" <-> "amo CRM", "API" <-> "A P I"). Ovozdagi qo'shimcha
    so'zlar (bog'lovchilar) tashlab ketiladi, ekrandagi mos kelmagan so'zlar qo'shnilar
    orasida interpolyatsiya qilinadi.
    """
    S = [norm(t) for t in show_tokens]
    V = [norm(w["text"]) for w in words]
    n, m = len(S), len(V)
    NEG = -1e9
    dp = np.full((n + 1, m + 1), NEG)
    bk = {}
    dp[0, :] = [-0.15 * j for j in range(m + 1)]
    for i in range(1, n + 1):
        dp[i, 0] = dp[i - 1, 0] - 0.5
        bk[(i, 0)] = ("s", 0)
        for j in range(1, m + 1):
            best, arg = dp[i - 1, j] - 0.5, ("s", 0)          # ekran so'zi mos kelmadi
            if dp[i, j - 1] - 0.15 > best:                       # ovozdagi ortiqcha so'z
                best, arg = dp[i, j - 1] - 0.15, ("v", 0)
            for k in range(1, 5):                                # 1..4 ovoz so'zi birlashadi
                if j - k < 0:
                    break
                cat = "".join(V[j - k:j])
                s = sim(S[i - 1], cat)
                if s >= 0.6:
                    sc = dp[i - 1, j - k] + 2 * s - (0.1 * (k - 1))
                    if sc > best:
                        best, arg = sc, ("m", k)
            dp[i, j] = best
            bk[(i, j)] = arg
    # oxirida ovozdagi qolgan so'zlarni tashlash mumkin
    j = int(np.argmax([dp[n, jj] - 0.15 * (m - jj) for jj in range(m + 1)]))
    i = n
    match = [None] * n
    while i > 0:
        op, k = bk.get((i, j), ("s", 0))
        if op == "m":
            match[i - 1] = (words[j - k]["start"], words[j - 1]["end"])
            i, j = i - 1, j - k
        elif op == "v":
            j -= 1
        else:
            i -= 1
    # faqat belgidan iborat so'zlar ("+", "→") o'qilmaydi — hisobga olinmaydi
    speakable = [k for k in range(n) if S[k]]
    matched = sum(1 for k in speakable if match[k])
    ratio = matched / max(1, len(speakable))
    total = words[-1]["end"] if words else 1.0
    # mos kelmaganlarni interpolyatsiya
    times = []
    for idx in range(n):
        if match[idx]:
            times.append(match[idx]); continue
        prev = next((match[p][1] for p in range(idx - 1, -1, -1) if match[p]), 0.0)
        nxt_i = next((p for p in range(idx + 1, n) if match[p]), None)
        nxt = match[nxt_i][0] if nxt_i is not None else total
        gap_n = (nxt_i if nxt_i is not None else n) - idx
        # shu oraliqdagi mos kelmagan so'zlar soni
        lo = idx
        while lo > 0 and not match[lo - 1]:
            lo -= 1
        cnt = gap_n + (idx - lo)
        pos = idx - lo
        seg = max(0.0, nxt - prev) / max(1, cnt)
        times.append((prev + pos * seg, prev + (pos + 1) * seg))
    return times, ratio


def proportional(show_tokens: list[str], dur: float) -> list[tuple[float, float]]:
    w = np.array([max(1, len(t)) + 1.5 for t in show_tokens], float)
    edges = np.concatenate([[0], np.cumsum(w)]) / w.sum() * dur
    return [(edges[k], edges[k + 1]) for k in range(len(show_tokens))]

# ----------------------------------------------------------------------------
# 3. Vaqt jadvali
# ----------------------------------------------------------------------------
@dataclass
class Chunk:
    role: str
    show: str
    say: str
    audio: np.ndarray = None
    words: list = None
    start: float = 0.0          # sahna ichidagi boshlanish (s)
    end: float = 0.0
    tokens: list = field(default_factory=list)
    times: list = field(default_factory=list)   # sahna ichidagi (start, end) har bir so'z uchun
    match_ratio: float = 1.0
    method: str = "wordboundary"


@dataclass
class Scene:
    idx: int
    tag: str
    title: str
    layout: str
    chunks: list
    start: float = 0.0
    dur: float = 0.0


def display_tokens(ch: Chunk) -> list[str]:
    if ch.role == "card":
        num, label = ch.show.split("|", 1)
        return [num] + label.split()
    return ch.show.split()


def build_timeline(scenes: list[Scene]) -> float:
    """Har bir bo'lak boshlanish/tugash vaqtini haqiqiy audio uzunligidan hisoblaydi."""
    t_abs = 0.0
    for sc in scenes:
        t = LEAD
        for ch in sc.chunks:
            d = len(ch.audio) / SR
            ch.start, ch.end = t, t + d
            ch.tokens = display_tokens(ch)
            tt, ratio = align(ch.tokens, ch.words) if ch.words else ([], 0.0)
            ch.match_ratio = ratio
            if ratio < 0.5 or not tt:
                tt = proportional(ch.tokens, d)
                ch.method = "proportional"
            ch.times = [(ch.start + a, ch.start + max(b, a + 0.08)) for a, b in tt]
            t = ch.end + GAP
        sc.dur = (t - GAP) + TAIL
        sc.start = t_abs
        t_abs += sc.dur
    return t_abs

# ----------------------------------------------------------------------------
# 4. Musiqa (yumshoq piano) va ducking
# ----------------------------------------------------------------------------

def _piano_note(freq: float, dur: float, vel: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for h, a in [(1, 1.0), (2, 0.42), (3, 0.18), (4, 0.09), (5, 0.04), (6, 0.02)]:
        f = freq * h * math.sqrt(1 + 0.0004 * h * h)       # yengil inharmoniklik
        if f > SR / 2:
            break
        dec = np.exp(-t * (1.1 + 0.9 * h) / max(0.6, dur * 0.5))
        out += a * dec * np.sin(2 * math.pi * f * t)
    att = np.minimum(1, t / 0.006)
    rel = np.minimum(1, (dur - t) / 0.25).clip(0, 1)
    return (out * att * rel * vel).astype(np.float32)


def _reverb(x: np.ndarray, seconds=2.2, mix=0.28) -> np.ndarray:
    rng = np.random.default_rng(7)
    n = int(seconds * SR)
    ir = rng.standard_normal(n).astype(np.float32) * np.exp(-np.arange(n) / SR * 3.2)
    ir[: int(0.012 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum())
    L = len(x) + n
    nfft = 1 << (L - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[: len(x)]
    return ((1 - mix) * x + mix * wet * 0.9).astype(np.float32)


def _add(buf: np.ndarray, s: int, x: np.ndarray):
    if s < 0:
        x, s = x[-s:], 0
    e = min(len(buf), s + len(x))
    if e > s:
        buf[s:e] += x[: e - s]


def make_music(total: float) -> np.ndarray:
    """Yumshoq piano: Cmaj7 – Am7 – Fmaj7 – G6 arpedjiolari, 72 BPM."""
    def hz(m):
        return 440 * 2 ** ((m - 69) / 12)
    prog = [[48, 55, 64, 67, 71], [45, 52, 60, 64, 67], [41, 48, 57, 60, 64], [43, 50, 59, 62, 64]]
    bpm = 72
    beat = 60 / bpm
    n = int((total + 3) * SR)
    mus = np.zeros(n, np.float32)
    rng = np.random.default_rng(3)
    bar = 0
    t = 0.0
    pattern = [0, 2, 3, 4, 3, 2, 1, 2]  # 8 ta yarim zarb
    while t < total + 1:
        ch = prog[bar % 4]
        # bas notasi
        s = int(t * SR)
        note = _piano_note(hz(ch[0] - 12 if ch[0] > 44 else ch[0]), beat * 4, 0.22)
        _add(mus, s, note)
        for k, p in enumerate(pattern):
            tt = t + k * beat / 2 + rng.uniform(-0.008, 0.008)
            s = int(tt * SR)
            if s >= n:
                break
            v = 0.13 + 0.03 * (k % 2 == 0) + rng.uniform(-0.015, 0.015)
            note = _piano_note(hz(ch[p]), beat * 2.2, v)
            _add(mus, s, note)
        t += beat * 4
        bar += 1
    mus = _reverb(mus)
    mus = mus[: int(total * SR)]
    # boshlanish va tugashda asta
    fi, fo = int(1.5 * SR), int(3.0 * SR)
    mus[:fi] *= np.linspace(0, 1, fi)
    mus[-fo:] *= np.linspace(1, 0, fo)
    return mus / (np.abs(mus).max() + 1e-9) * 0.5


def duck_gain(narr: np.ndarray, base_db=-17.0, duck_db=-31.0, attack=0.12, release=0.9) -> np.ndarray:
    """Ovoz bor joyda musiqa pasayadi, ovoz bo'lmaganda asta ko'tariladi."""
    hop = SR // 100
    nfr = len(narr) // hop + 1
    pad = np.pad(narr, (0, nfr * hop - len(narr)))
    rms = np.sqrt((pad.reshape(nfr, hop) ** 2).mean(1) + 1e-12)
    active = (20 * np.log10(rms) > -42).astype(float)
    # 250 ms ichida yana ovoz bo'lsa, pastda tursin (so'zlar orasida "nasos" bo'lmasin)
    k = 25
    act = np.convolve(active, np.ones(2 * k + 1), "same") > 0
    target = np.where(act, duck_db, base_db)
    g = np.empty(nfr)
    cur = base_db
    a_c = 1 - math.exp(-0.01 / attack)
    r_c = 1 - math.exp(-0.01 / release)
    for i in range(nfr):
        c = a_c if target[i] < cur else r_c
        cur += (target[i] - cur) * c
        g[i] = cur
    lin = 10 ** (g / 20)
    return np.interp(np.arange(len(narr)), np.arange(nfr) * hop, lin).astype(np.float32)

# ----------------------------------------------------------------------------
# 5. Chizish (dizayn v2/v3 dan o'lchangan)
# ----------------------------------------------------------------------------
_fonts = {}


def F(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    key = (bold, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(FONT_B if bold else FONT_R, size)
    return _fonts[key]


def mix(c1, c2, k):
    return tuple(int(round(a * k + b * (1 - k))) for a, b in zip(c1, c2))


BG = np.asarray(Image.open(HERE / "assets" / "bg_plate.png").convert("RGB"))
BG_AVG = tuple(int(x) for x in BG.reshape(-1, 3).mean(0))


@dataclass
class WordBox:
    text: str
    x: float
    y: float          # matn yuqori nuqtasi (draw.text y)
    font: object
    color: tuple      # asl (o'qilgan) rang
    t0: float
    t1: float


@dataclass
class Deco:
    """Bo'lakka bog'liq bezak (karta/quti ramkasi, strelka, marker) — bo'lak boshlanganda yorishadi."""
    kind: str
    box: tuple
    t0: float


def text_top(font, y_top: float, ref="Kk'lI") -> float:
    return y_top - font.getbbox(ref)[1]


def place_line(tokens, font, x0, y_top, color, times, out):
    x = x0
    y = text_top(font, y_top)
    sp = font.getlength(" ")
    for tok, (a, b) in zip(tokens, times):
        out.append(WordBox(tok, x, y, font, color, a, b))
        x += font.getlength(tok) + sp


def wrap(tokens, font, maxw):
    lines, cur = [], []
    for t in tokens:
        trial = " ".join(cur + [t])
        if cur and font.getlength(trial) > maxw:
            lines.append(cur); cur = [t]
        else:
            cur.append(t)
    if cur:
        lines.append(cur)
    return lines


def place_centered(tokens, times, font, cx, y_top, line_h, maxw, color, out):
    lines = wrap(tokens, font, maxw)
    k = 0
    for li, line in enumerate(lines):
        w = font.getlength(" ".join(line))
        place_line(line, font, cx - w / 2, y_top + li * line_h, color, times[k:k + len(line)], out)
        k += len(line)
    return len(lines)


def layout_scene(sc: Scene, total_scenes: int):
    """Statik qatlam (fon, sarlavha) + so'z qutilari + bezaklar."""
    base = Image.fromarray(BG.copy())
    d = ImageDraw.Draw(base)
    d.rectangle([0, 0, 5, H], fill=BLUE)                       # chap chiziq
    fnt_footer = F(False, 20)
    d.text((70, text_top(fnt_footer, 678, "U")), "Urgut Hills AI Dashboard", font=fnt_footer, fill=MUTED)
    words, decos = [], []

    if sc.layout != "cover":
        fh = F(True, 20)
        d.text((70, text_top(fh, 48, "0")), f"{sc.idx:02d} / {total_scenes}   {sc.tag}", font=fh, fill=BLUE)
        ft = F(True, 50)
        d.text((70, text_top(ft, 85, "Ak")), sc.title, font=ft, fill=TITLE_C)
        d.rectangle([70, 146, 191, 149], fill=BLUE)

    if sc.layout == "cover":
        for ch in sc.chunks:
            if ch.role == "big":
                place_centered(ch.tokens, ch.times, F(True, 83), W / 2, 234, 90, 1200, TITLE_C, words)
            elif ch.role == "sub":
                place_centered(ch.tokens, ch.times, F(False, 34), W / 2, 381, 40, 1100, TEXT_C, words)
            elif ch.role == "note":
                place_centered(ch.tokens, ch.times, F(False, 30), W / 2, 460, 38, 1100, MUTED, words)
        d.rectangle([550, 334, 731, 339], fill=BLUE)

    elif sc.layout == "bullets":
        y = 196
        fb = F(False, 34)
        for ch in sc.chunks:
            if ch.role == "sub":
                place_line(ch.tokens, F(False, 30), 70, 195, MUTED, ch.times, words)
                y = 256
                continue
            decos.append(Deco("square", (70, y + 8, 84, y + 22), ch.start))
            place_line(ch.tokens, fb, 105, y, TEXT_C, ch.times, words)
            y += 72

    elif sc.layout == "cards":
        for k, ch in enumerate(sc.chunks):
            x0 = 60 + 300 * k
            decos.append(Deco("card", (x0, 250, x0 + 261, 521), ch.start))
            cx = x0 + 130.5
            fn = F(True, 86)
            num = ch.tokens[0]
            words.append(WordBox(num, cx - fn.getlength(num) / 2, text_top(fn, 297, "8"), fn, BLUE,
                                 *ch.times[0]))
            place_centered(ch.tokens[1:], ch.times[1:], F(False, 24), cx, 405, 32, 225, MUTED, words)

    elif sc.layout in ("flow", "arch"):
        boxes = [c for c in sc.chunks if c.role == "box"]
        caps = [c for c in sc.chunks if c.role == "caption"]
        n = len(boxes)
        gapx = 50
        bw = min(260.0, (1160 - gapx * (n - 1)) / n)
        x_start = 640 - (n * bw + gapx * (n - 1)) / 2
        fbx = F(True, 26)
        for k, ch in enumerate(boxes):
            x0 = x_start + k * (bw + gapx)
            decos.append(Deco("box", (x0, 230, x0 + bw, 381), ch.start))
            if k:
                decos.append(Deco("arrow", (x0 - gapx + 7, 305.5, x0 - 5, 305.5), ch.start))
            lines = wrap(ch.tokens, fbx, bw - 22)
            top = 305.5 - (len(lines) * 34 - 8) / 2 - 2
            place_centered(ch.tokens, ch.times, fbx, x0 + bw / 2, top, 34, bw - 22, TEXT_C, words)
        fc = F(False, 30)
        for k, ch in enumerate(caps):
            place_centered(ch.tokens, ch.times, fc, 640, 445 + 40 * k, 40, 1150, MUTED, words)
    return base, words, decos


def draw_deco(img: Image.Image, dc: Deco, t: float):
    k = 0.35 + 0.65 * smooth((t - dc.t0 + 0.15) / 0.35)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    a = int(255 * k)
    x0, y0, x1, y1 = dc.box
    if dc.kind == "square":
        od.rectangle([x0, y0, x1, y1], fill=GREEN + (a,))
    elif dc.kind == "card":
        od.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=CARD_FILL + (int(235 * k),),
                             outline=BLUE + (a,), width=2)
    elif dc.kind == "box":
        od.rounded_rectangle([x0, y0, x1, y1], radius=14, fill=CARD_FILL + (int(235 * k),),
                             outline=BLUE + (a,), width=4)
    elif dc.kind == "arrow":
        od.rectangle([x0, y0 - 2, x1 - 9, y0 + 1], fill=BLUE + (a,))
        od.polygon([(x1 - 11, y0 - 7), (x1, y0 - 0.5), (x1 - 11, y0 + 6)], fill=BLUE + (a,))
    img.alpha_composite(ov)


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


_glyph_cache = {}


def word_sprite(text, font, color):
    key = (text, id(font), color)
    if key not in _glyph_cache:
        l, tp, r, b = font.getbbox(text)
        pad = 12
        im = Image.new("RGBA", (int(r - l) + 2 * pad, int(b) + 2 * pad), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((pad - l, pad), text, font=font, fill=color + (255,))
        _glyph_cache[key] = (im, pad - l, pad)
    return _glyph_cache[key]


def render_frame(base_rgba, words, decos, t, scene_dur):
    img = base_rgba.copy()
    for dc in decos:
        draw_deco(img, dc, t)
    d = ImageDraw.Draw(img)
    for wb in words:
        dim = mix(wb.color, BG_AVG, DIM_K)
        if t < wb.t0 - 0.06:
            d.text((wb.x, wb.y), wb.text, font=wb.font, fill=dim)
            continue
        if t >= wb.t1 + 0.12:
            d.text((wb.x, wb.y), wb.text, font=wb.font, fill=wb.color)
            continue
        if t < wb.t1:
            # o'qilmoqda: ko'k rangga o'tadi va biroz tebranadi
            k_in = smooth((t - (wb.t0 - 0.06)) / 0.10)
            col = mix(BLUE, dim, k_in)
            ph = (t - wb.t0) * 2 * math.pi * 6.0
            amp = k_in
            dy = -2.2 * amp * abs(math.sin(ph * 0.5))
            ang = 2.2 * amp * math.sin(ph)
            sc_ = 1.0 + 0.06 * amp
        else:
            k_out = smooth((t - wb.t1) / 0.12)
            col = mix(wb.color, BLUE, k_out)
            dy, ang, sc_ = 0.0, 0.0, 1.0 + 0.06 * (1 - k_out)
        if abs(ang) < 0.05 and abs(sc_ - 1) < 0.004 and abs(dy) < 0.2:
            d.text((wb.x, wb.y), wb.text, font=wb.font, fill=col)
            continue
        spr, ox, oy = word_sprite(wb.text, wb.font, col)
        cw, chh = spr.size
        s2 = spr.resize((max(1, int(cw * sc_)), max(1, int(chh * sc_))), Image.BICUBIC)
        s2 = s2.rotate(ang, resample=Image.BICUBIC, expand=True)
        cx = wb.x - ox + cw / 2
        cy = wb.y - oy + chh / 2 + dy
        img.alpha_composite(s2, (int(round(cx - s2.size[0] / 2)), int(round(cy - s2.size[1] / 2))))
    # sahna progress chizig'i
    pw = int(W * min(1.0, t / scene_dur))
    if pw > 0:
        d.rectangle([0, 716, pw, 719], fill=BLUE)
    # qora fondan chiqish / kirish
    fade = min(smooth(t / FADE), smooth((scene_dur - t) / FADE))
    rgb = img.convert("RGB")
    if fade < 0.999:
        arr = (np.asarray(rgb).astype(np.float32) * fade).astype(np.uint8)
        return arr
    return np.asarray(rgb)


def render_scene(sc: Scene, total_scenes: int, path: Path):
    base, words, decos = layout_scene(sc, total_scenes)
    base_rgba = base.convert("RGBA")
    nframes = int(round(sc.dur * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-r", str(FPS), "-movflags", "+faststart", str(path)], stdin=subprocess.PIPE)
    for f in range(nframes):
        t = (f + 0.5) / FPS
        p.stdin.write(render_frame(base_rgba, words, decos, t, sc.dur).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError(f"sahna {sc.idx} renderi xato")
    return nframes / FPS

# ----------------------------------------------------------------------------
# 6. Asosiy oqim
# ----------------------------------------------------------------------------

def write_wav(path: Path, x: np.ndarray, ch=1):
    y = np.clip(x, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(ch); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/mnt/user-data/outputs/urgut-hills-loyiha-v4.mp4")
    ap.add_argument("--work", default=str(HERE / "build"))
    ap.add_argument("--only", type=int, nargs="*", help="faqat shu sahnalarni render qilish (test)")
    args = ap.parse_args()
    out = Path(args.out)
    work = Path(args.work)
    (work / "tts").mkdir(parents=True, exist_ok=True)
    (work / "scenes").mkdir(parents=True, exist_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)

    scenes = []
    for si, (tag, title, layout, items) in enumerate(SCENES, 1):
        chunks = []
        for ci, (role, show, say) in enumerate(items):
            audio, words = synth_chunk(say, work / "tts", f"s{si:02d}_c{ci:02d}")
            chunks.append(Chunk(role, show, say, audio, words))
        scenes.append(Scene(si, tag, title, layout, chunks))
        print(f"TTS: sahna {si:02d} tayyor ({len(chunks)} bo'lak)")
    total = build_timeline(scenes)
    # kadrlarga yaxlitlash: video va audio aynan bir xil uzunlikda bo'lsin
    t_abs = 0.0
    for sc in scenes:
        sc.dur = round(sc.dur * FPS) / FPS
        sc.start = t_abs
        t_abs += sc.dur
    total = t_abs

    # --- audio ---
    narr = np.zeros(int(total * SR) + SR, np.float32)
    for sc in scenes:
        for ch in sc.chunks:
            s = int(round((sc.start + ch.start) * SR))
            narr[s:s + len(ch.audio)] += ch.audio
    narr = narr[: int(round(total * SR))]
    peak = np.abs(narr).max()
    narr_n = narr / peak * 0.89                       # -1 dBFS
    narration_wav = out.with_name(out.stem + "-narration.wav")
    write_wav(narration_wav, narr_n)
    music = make_music(total)
    music = music[: len(narr_n)]
    music = np.pad(music, (0, len(narr_n) - len(music)))
    g = duck_gain(narr_n)
    music_wav = out.with_name(out.stem + "-music.wav")
    write_wav(music_wav, music * 10 ** (-17 / 20))
    mixed = narr_n + music * g
    pre = work / "mix_pre.wav"
    write_wav(pre, mixed / max(1.0, np.abs(mixed).max()))
    # loudnorm (2 bosqich)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af",
                        "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    final_wav = work / "mix_final.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af",
                    f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
                    f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:"
                    f"offset={js['target_offset']}:linear=true,aresample={SR}",
                    "-ac", "2", "-c:a", "pcm_s16le", str(final_wav)], check=True)

    # --- video ---
    only = set(args.only or [])
    lst = work / "scenes" / "list.txt"
    with open(lst, "w") as f:
        for sc in scenes:
            p = work / "scenes" / f"scene_{sc.idx:02d}.mp4"
            if not only or sc.idx in only:
                render_scene(sc, len(scenes), p)
                print(f"render: sahna {sc.idx:02d}  {sc.dur:6.2f}s")
            f.write(f"file '{p}'\n")
    if only:
        return
    video_only = work / "video_only.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(video_only)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video_only), "-i", str(final_wav),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-ar", str(SR), "-shortest", "-movflags", "+faststart", str(out)], check=True)

    # --- hisobot ---
    report = {"voice": VOICE, "total_sec": round(total, 2), "LEAD": LEAD, "GAP": GAP, "TAIL": TAIL,
              "scenes": []}
    for sc in scenes:
        report["scenes"].append({
            "scene": sc.idx, "title": sc.title or sc.chunks[0].show, "start": round(sc.start, 2),
            "dur": round(sc.dur, 2),
            "chunks": [{"show": ch.show, "say": ch.say, "start": round(sc.start + ch.start, 2),
                        "end": round(sc.start + ch.end, 2), "match": round(ch.match_ratio, 2),
                        "method": ch.method} for ch in sc.chunks]})
    (out.with_name(out.stem + "-timeline.json")).write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"Tayyor: {out}  ({total:.1f}s)")


if __name__ == "__main__":
    main()
