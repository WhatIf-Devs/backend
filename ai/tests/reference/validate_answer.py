"""AI 답변 검증기 참조 구현 (정책표 9장: 숫자 검증, 금지 표현, 문체).

실행은 BE 모듈에서 하고, 이 파일은 규칙을 코드로 못박아 두는 기준이다.
허용 숫자 집합 밖의 숫자가 하나라도 나오면 실패 → 재생성(최대 2회) → 폴백.
"""
from __future__ import annotations

import re

FORBIDDEN = ["반드시", "무조건", "확실히", "추천", "가장 좋은", "1위", "보장", "투자하"]
INTEREST_WORDS = ["이자", "금리", "세금", "수익률"]

LIMITS = {  # kind: (최대 문장 수, 최대 글자 수)
    "change.answerText": (2, 120),
    "change.summaryText": (1, 80),
    "explainResult": (3, 160),
    "explainTerm": (3, 160),
    "summary": (1, 80),
    "scenarioName": (None, 30),
}


def _num(s: str) -> float:
    return float(s.replace(",", ""))


PATTERNS = [  # (종류, 정규식, 값 함수) — 위에서부터 차례로 지운다
    ("money", r"(\d[\d,]*)\s*억\s*(?:(\d[\d,]*)\s*만\s*)?원", lambda m: _num(m[1]) * 10000 + (_num(m[2]) if m[2] else 0)),
    ("money", r"(\d[\d,]*)\s*만\s*(\d)\s*천\s*원", lambda m: _num(m[1]) + int(m[2]) / 10),
    ("money", r"(\d[\d,]*(?:\.\d+)?)\s*만\s*원", lambda m: _num(m[1])),
    ("money", r"(\d)\s*천\s*원", lambda m: int(m[1]) / 10),
    ("percent", r"(\d+(?:\.\d+)?)\s*%", lambda m: _num(m[1])),
    ("ym", r"(\d{4})\s*년\s*(\d{1,2})\s*월", lambda m: f"{int(m[1]):04d}-{int(m[2]):02d}"),
    ("year", r"(\d{4})\s*년", lambda m: int(m[1])),
    ("periodYears", r"(\d{1,2})\s*년", lambda m: int(m[1]) * 12),
    ("periodMonths", r"(\d{1,3})\s*개월", lambda m: int(m[1])),
    ("month", r"(\d{1,2})\s*월", lambda m: int(m[1])),
    ("version", r"[Vv]\s*(\d{1,2})", lambda m: int(m[1])),
]


def extract(text: str) -> list[tuple[str, object, str]]:
    t = text.replace("−", "-").replace("–", "-")
    found = []
    for kind, pat, fn in PATTERNS:
        def repl(m):
            found.append((kind, fn(m), m.group(0)))
            return " " * len(m.group(0))
        t = re.sub(pat, repl, t)
    for m in re.finditer(r"\d+", t):
        found.append(("unknown", m.group(0), m.group(0)))
    return found


def sentences(text: str) -> int:
    parts = [p for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p.strip()]
    return len(parts)


def check(text: str | None, kind: str, allowed: dict) -> dict:
    """allowed = {amountsMan, percents, months(YYYY-MM), periods(개월), versions}."""
    reasons = []
    if text is None or not text.strip():
        return {"pass": False, "reasons": ["empty"]}
    amounts = {round(abs(float(a)), 1) for a in allowed.get("amountsMan", [])}
    months = set(allowed.get("months", []))
    years = {int(m[:4]) for m in months}
    moy = {int(m[5:]) for m in months}
    periods = set(allowed.get("periods", []))

    no_digits = kind == "explainTerm"
    for k, v, raw in extract(text):
        if no_digits:
            reasons.append(f"number_in_term:{raw}")
        elif k == "money" and round(abs(v), 1) not in amounts:
            reasons.append(f"amount_mismatch:{raw}")
        elif k == "percent" and v not in set(allowed.get("percents", [])):
            reasons.append(f"percent_not_allowed:{raw}")
        elif k == "ym" and v not in months:
            reasons.append(f"month_mismatch:{raw}")
        elif k == "year" and v not in years:
            reasons.append(f"year_mismatch:{raw}")
        elif k in ("periodYears", "periodMonths") and v not in periods:
            reasons.append(f"period_mismatch:{raw}")
        elif k == "month" and v not in moy:
            reasons.append(f"month_mismatch:{raw}")
        elif k == "version" and v not in set(allowed.get("versions", [])):
            reasons.append(f"version_mismatch:{raw}")
        elif k == "unknown":
            reasons.append(f"unknown_number:{raw}")

    for w in FORBIDDEN:
        if w in text:
            reasons.append(f"forbidden_phrase:{w}")
    if "세요" in text:
        reasons.append("imperative")
    if kind not in ("explainTerm",) and any(w in text for w in INTEREST_WORDS):
        reasons.append("interest_mention")
    max_s, max_len = LIMITS[kind]
    if max_s and sentences(text) > max_s:
        reasons.append("too_many_sentences")
    if len(text) > max_len:
        reasons.append("too_long")
    if kind != "scenarioName" and not re.search(r"(요|죠)[.!?]?$", text.strip()):
        reasons.append("not_haeyo")
    return {"pass": not reasons, "reasons": reasons}


# ---------- 허용 숫자 집합 만들기 (서버가 AI 입력에서 만드는 방식의 참조) ----------
def _walk_numbers(obj, out_amounts, out_months):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("achievementRate", "periodMonths", "versionNo", "no", "versionNos", "repeat"):
                continue
            _walk_numbers(v, out_amounts, out_months)
    elif isinstance(obj, list):
        for v in obj:
            _walk_numbers(v, out_amounts, out_months)
    elif isinstance(obj, bool) or obj is None:
        return
    elif isinstance(obj, (int, float)):
        out_amounts.add(abs(obj))
    elif isinstance(obj, str) and re.fullmatch(r"\d{4}-\d{2}", obj):
        out_months.add(obj)


def allowed_from_input(ai_input: dict) -> dict:
    """AI에 넘긴 입력 안의 금액·달·비율·기간·버전만 허용한다."""
    amounts, months, percents, periods, versions = set(), set(), set(), set(), set()
    _walk_numbers(ai_input, amounts, months)

    def collect(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "achievementRate" and v is not None:
                    percents.add(v)
                elif k == "periodMonths" and isinstance(v, int):
                    periods.add(v)
                elif k in ("versionNo", "no") and isinstance(v, int):
                    versions.add(v)
                elif k == "monthsToDeadline" and isinstance(v, int):
                    periods.add(v)
                collect(v)
        elif isinstance(o, list):
            for v in o:
                collect(v)
    collect(ai_input)
    return {"amountsMan": sorted(amounts), "percents": sorted(percents), "months": sorted(months),
            "periods": sorted(periods), "versions": sorted(versions)}
