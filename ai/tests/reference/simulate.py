"""What If? 계산 엔진 참조 구현 (API 01 POST /api/v1/simulations 재현용).

BE 구현을 대신하는 코드가 아니라, AI 파트가 테스트 기대값과 AI 입력 예시를
만들 때 쓰는 기준 구현이다. 계산식은 정책표 3장과 API 명세 01 비고를 따른다.

  A(0) = 현재 자산
  A(m) = A(m-1) + 월 저축 + 그달 이벤트 합계   (저축은 1개월차부터, 이자·세금 미반영)

명세에 정의가 없어 추정한 부분은 ASSUMPTION 주석으로 표시했다. BE와 맞춰 확인할 것.
"""
from __future__ import annotations

import copy
import math

RANGES = {
    "periodMonths": (6, 120),
    "currentAsset": (0, 100000),
    "monthlySaving": (0, 1000),
    "eventAmount": (1, 100000),
    "goalAmount": (1, 1000000),
}


# ---------- 월 계산 ----------
def ym_to_index(ym: str) -> int:
    y, m = ym.split("-")
    return int(y) * 12 + int(m) - 1


def index_to_ym(i: int) -> str:
    return f"{i // 12:04d}-{i % 12 + 1:02d}"


def add_months(ym: str, n: int) -> str:
    return index_to_ym(ym_to_index(ym) + n)


def offset(start: str, ym: str) -> int:
    """start 기준 몇 개월차인지 (start 자체는 0)."""
    return ym_to_index(ym) - ym_to_index(start)


# ---------- 조건 검증 (공통 규칙: 검증 에러는 필드별 코드, 여러 개가 틀려도 첫 번째 하나만) ----------
# 확인된 코드: CONDITION400_3 = 현재 자산, CONDITION400_12 = 목표 기한(계산 기간 밖).
# 나머지 번호는 Condition 필드 순서로 추정했다 (ASSUMPTION, 공통 규칙 3장으로 확인할 것).
# 기간 밖 이벤트는 에러가 아니라 warnings (API 01 비고).
CONDITION_CODES = [
    ("CONDITION400_1", "startMonth", None),
    ("CONDITION400_2", "periodMonths", None),
    ("CONDITION400_3", "currentAsset", "현재 자산은 0~100,000만원으로 입력해 주세요."),
    ("CONDITION400_4", "monthlySaving", None),
    ("CONDITION400_5", "events[].name", None),
    ("CONDITION400_6", "events[].type", None),
    ("CONDITION400_7", "events[].amount", None),
    ("CONDITION400_8", "events[].month", None),
    ("CONDITION400_9", "events[].repeat", None),
    ("CONDITION400_10", "goal.name", None),
    ("CONDITION400_11", "goal.amount", None),
    ("CONDITION400_12", "goal.deadline", "목표 기한이 계산 기간을 벗어나요."),
]
_CODE_OF = {f: code for code, f, _ in CONDITION_CODES}
_MSG_OF = {code: msg for code, _, msg in CONDITION_CODES}


def _is_ym(v) -> bool:
    import re
    return isinstance(v, str) and re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", v) is not None


def validate_condition(c: dict) -> list[str]:
    """틀린 필드를 Condition 필드 순서대로 모두 돌려준다 (내부 점검용)."""
    errs = []
    if not _is_ym(c.get("startMonth")):
        errs.append("startMonth")
    lo, hi = RANGES["periodMonths"]
    if not lo <= c["periodMonths"] <= hi:
        errs.append("periodMonths")
    lo, hi = RANGES["currentAsset"]
    if not lo <= c["currentAsset"] <= hi:
        errs.append("currentAsset")
    lo, hi = RANGES["monthlySaving"]
    if not lo <= c["monthlySaving"] <= hi:
        errs.append("monthlySaving")
    for e in c.get("events") or []:
        if not 1 <= len(e["name"]) <= 20:
            errs.append("events[].name")
        if e["type"] not in ("income", "expense"):
            errs.append("events[].type")
        lo, hi = RANGES["eventAmount"]
        if not lo <= e["amount"] <= hi:
            errs.append("events[].amount")
        if not _is_ym(e["month"]):
            errs.append("events[].month")
        if e["repeat"] not in ("once", "monthly"):
            errs.append("events[].repeat")
    g = c.get("goal")
    if g:
        if g.get("name") is not None and not 1 <= len(g["name"]) <= 20:
            errs.append("goal.name")
        lo, hi = RANGES["goalAmount"]
        if not lo <= g["amount"] <= hi:
            errs.append("goal.amount")
        d = offset(c["startMonth"], g["deadline"]) if _is_ym(g.get("deadline")) else 0
        if d < 1 or d > c["periodMonths"]:
            errs.append("goal.deadline")
    order = [f for _, f, _ in CONDITION_CODES]
    return sorted(dict.fromkeys(errs), key=order.index)


def first_condition_error(c: dict):
    """API가 내려 줄 검증 에러 하나 (없으면 None). 공통 응답 형태로 반환."""
    errs = validate_condition(c)
    if not errs:
        return None
    code = _CODE_OF[errs[0]]
    return {"isSuccess": False, "code": code, "message": _MSG_OF[code] or f"({errs[0]} 범위 안내 문구: 공통 규칙 3장 확인)", "result": None}


# ---------- 계산 ----------
def _event_amount_at(events, start, m):
    total = 0
    for e in events:
        k = offset(start, e["month"])
        sign = 1 if e["type"] == "income" else -1
        if e["repeat"] == "once" and k == m:
            total += sign * e["amount"]
        elif e["repeat"] == "monthly" and k <= m:
            total += sign * e["amount"]
    return total


def _series(c, events, horizon):
    s = [c["currentAsset"]]
    for m in range(1, horizon + 1):
        s.append(s[-1] + c["monthlySaving"] + _event_amount_at(events, c["startMonth"], m))
    return s


def simulate(c: dict) -> dict:
    errs = validate_condition(c)
    if errs:
        raise ValueError(errs)
    start, P = c["startMonth"], c["periodMonths"]
    inside, warnings = [], []
    for e in c.get("events") or []:
        k = offset(start, e["month"])
        if 1 <= k <= P:
            inside.append(e)
        else:
            warnings.append({"eventId": e.get("id"), "name": e["name"], "month": e["month"]})  # ASSUMPTION: warnings 항목 모양

    series = _series(c, inside, P)
    event_total = sum(series[i] - series[i - 1] - c["monthlySaving"] for i in range(1, P + 1))

    goal_out = None
    g = c.get("goal")
    if g:
        d = offset(start, g["deadline"])
        at = series[d]
        shortfall = g["amount"] - at
        already = c["currentAsset"] >= g["amount"]
        reached = None
        if not already:
            for m in range(1, d + 1):
                if series[m] >= g["amount"]:
                    reached = add_months(start, m)
                    break
        extra = None
        if shortfall > 0:
            # 정책표 3장: 부족액 ÷ 기한까지 남은 저축 횟수, 천원(0.1만원) 단위 반올림
            extra = math.floor(shortfall / d * 10 + 0.5) / 10
        goal_out = {
            "assetAtDeadline": at,
            "shortfall": shortfall,
            "achievementRate": math.floor(at / g["amount"] * 100 + 0.5),
            "extraSavingNeeded": extra,          # ASSUMPTION: 부족하지 않으면 null
            "reachedMonth": reached,             # ASSUMPTION: 기한 안에 못 닿거나 이미 달성이면 null
            "alreadyAchieved": already,
        }

    negative = None
    for m, a in enumerate(series):
        if a < 0:
            negative = {"month": add_months(start, m), "asset": a}  # ASSUMPTION: negativeAsset 모양
            break

    # ASSUMPTION: milestones는 기간과 무관하게 같은 조건을 12·60개월까지 연장한 값
    # (명세 예시: 기간 12개월인데 after5Years 2850 = 500 + 40×60 + 100 − 150)
    long_events = [e for e in (c.get("events") or []) if offset(start, e["month"]) >= 1]
    ext = _series(c, long_events, max(P, 60))
    return {
        "series": series,
        "summary": {
            "finalAsset": series[P],
            "increase": series[P] - c["currentAsset"],
            "totalSaving": c["monthlySaving"] * P,
            "eventTotal": event_total,
            "goal": goal_out,
            "negativeAsset": negative,
            "milestones": {"after1Year": ext[12], "after5Years": ext[60]},
        },
        "warnings": warnings,
    }


def situation(c: dict, r: dict) -> str:
    g = r["summary"]["goal"]
    if not g:
        return "no_goal"
    if g["alreadyAchieved"]:
        return "goal_already"
    if g["shortfall"] > 0:
        return "goal_short"
    if g["shortfall"] < 0:
        return "goal_excess"
    return "goal_exact"


def declines(c: dict, r: dict) -> list[dict]:
    """자산이 전달보다 줄어든 달 (explainResult 입력용)."""
    s = r["series"]
    return [{"month": add_months(c["startMonth"], m), "delta": s[m] - s[m - 1]}
            for m in range(1, len(s)) if s[m] < s[m - 1]]


def top_driver(c: dict, r: dict) -> dict:
    """한줄요약의 '가장 큰 원인' (제안: 서버가 고르고 AI는 문장만 쓴다).

    - 목표 부족이거나 자산이 음수가 되면: 영향(impact)이 가장 큰 지출 이벤트, 없으면 월 저축
    - 그 외: 월 저축 누적과 수입 이벤트 중 영향이 가장 큰 것
    """
    start, P = c["startMonth"], c["periodMonths"]
    items = []
    for e in c.get("events") or []:
        k = offset(start, e["month"])
        if not 1 <= k <= P:
            continue
        times = 1 if e["repeat"] == "once" else P - k + 1
        sign = 1 if e["type"] == "income" else -1
        items.append({"kind": "event", "name": e["name"], "month": e["month"], "amount": sign * e["amount"],
                      "repeat": e["repeat"], "impact": sign * e["amount"] * times})
    saving = {"kind": "saving", "name": "월 저축", "month": None, "amount": c["monthlySaving"],
              "repeat": "monthly", "impact": r["summary"]["totalSaving"]}
    sit = situation(c, r)
    if sit == "goal_short" or r["summary"]["negativeAsset"]:
        neg = [i for i in items if i["impact"] < 0]
        if neg:
            return min(neg, key=lambda i: (i["impact"], i["month"]))
        return saving
    pos = [i for i in items if i["impact"] > 0] + [saving]
    return max(pos, key=lambda i: i["impact"])


# ---------- 서버가 AI 해석 결과를 조건에 적용 (참조) ----------
def apply_change(versions: list[dict], base_no: int, change: dict, new_event_id) -> dict:
    src_no = change.get("fromVersionNo") or base_no
    base = next(v for v in versions if v["no"] == src_no)["condition"]
    c = copy.deepcopy(base)
    ms = change.get("monthlySaving")
    if ms:
        c["monthlySaving"] = c["monthlySaving"] + ms["value"] if ms["mode"] == "delta" else ms["value"]
    for op in change.get("events") or []:
        if op["op"] == "add":
            c["events"].append({"id": new_event_id(), "name": op["name"], "type": op["type"],
                                "amount": op["amount"], "month": op["month"], "repeat": op["repeat"]})
        else:
            idx = next(i for i, e in enumerate(c["events"]) if e["id"] == op["eventId"])
            if op["op"] == "delete":
                c["events"].pop(idx)
            else:
                for k in ("name", "type", "amount", "month", "repeat"):
                    if op.get(k) is not None:
                        c["events"][idx][k] = op[k]
    g = change.get("goal")
    if g:
        if g["op"] == "remove":
            c["goal"] = None
        elif g["op"] == "set":
            c["goal"] = {"name": g.get("name") or "내 목표", "amount": g["amount"], "deadline": g["deadline"]}
        else:
            c["goal"] = dict(c["goal"])
            for k in ("name", "amount", "deadline"):
                if g.get(k) is not None:
                    c["goal"][k] = g[k]
    if change.get("periodMonths") is not None:
        c["periodMonths"] = change["periodMonths"]
    if change.get("solveFor") == "monthlySaving":
        c["monthlySaving"] = solve_monthly_saving(c)
    return c


def solve_monthly_saving(c: dict) -> int:
    """목표 기한에 목표 금액이 되는 최소 월 저축 (ASSUMPTION: 만원 정수 올림. PM 확인 중)."""
    g = c["goal"]
    d = offset(c["startMonth"], g["deadline"])
    zero = dict(c, monthlySaving=0)
    inside = [e for e in c["events"] if 1 <= offset(c["startMonth"], e["month"]) <= c["periodMonths"]]
    base_at = _series(zero, inside, d)[d]
    need = g["amount"] - base_at
    return max(0, math.ceil(need / d))
