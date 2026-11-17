"""AI 파트 산출물 자체 검사. 실행: python tests/reference/run_all.py (WhatIf_v0 폴더에서)

1. 골든 계산 (API 명세 01 비고)
2. 검증기 단위 테스트 (tests/validator.cases.json)
3. 해석 정답지·시험 질문의 change가 서버 적용 후 유효한 조건이 되는지
4. 예시 답변이 검증을 통과하는지
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import simulate as S  # noqa: E402
import validate_answer as V  # noqa: E402


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


fails = 0


def ok(cond, msg):
    global fails
    if not cond:
        fails += 1
        print("FAIL", msg)


# 1. 골든
for case in load("tests/golden.simulation.json")["cases"]:
    exp = case["expect"]
    if "solveMonthlySaving" in exp:
        ok(S.solve_monthly_saving(case["condition"]) == exp["solveMonthlySaving"], case["name"])
        continue
    r = S.simulate(case["condition"])
    s, g = r["summary"], r["summary"]["goal"] or {}
    for k, v in exp.items():
        got = {"series": r["series"], "finalAsset": s["finalAsset"], "negativeAsset": s["negativeAsset"],
               "after5Years": s["milestones"]["after5Years"]}.get(k, g.get(k))
        ok(got == v, f"golden {case['name']} {k}: {got} != {v}")

# 2. 검증기
for c in load("tests/validator.cases.json")["cases"]:
    r = V.check(c["answer"], c["kind"], c["allowed"])
    ok(r["pass"] == c["expectedPass"], f"validator #{c['id']} pass={r['pass']} {r['reasons']}")
    for p in c["expectedReasonPrefixes"]:
        ok(any(x.startswith(p) for x in r["reasons"]), f"validator #{c['id']} missing {p}: {r['reasons']}")

# 3. change 적용
fx = load("schema/fixtures/chat-requests.json")["fixtures"]
qs = load("tests/questions.json")["questions"]
for q in qs:
    cands = ([q["expected"]] if q["expected"] else []) + q.get("alternatives", [])
    for e in cands:
        ok(e["type"] == q["expectedType"], f"q{q['id']} type")
        for t in ("change", "explain", "clarify", "finance", "refuse"):
            ok((e[t] is not None) == (t == e["type"]), f"q{q['id']} only {e['type']} object")
        if e["type"] != "change":
            continue
        f = fx[q["fixture"]]
        n = iter(range(100, 200))
        new = S.apply_change(f["versions"], f["baseVersionNo"], e["change"], lambda: f"ev-{next(n)}")
        errs = S.validate_condition(new)
        ok(not errs, f"q{q['id']} {q['question']} → {errs}")
        if q["id"] == 1:
            ok(S.simulate(new)["summary"]["finalAsset"] == 1050, "q1 1050")
        if q["id"] == 4:
            ok(new["monthlySaving"] == 55, "q4 solve 55")

# 4. 예시 답변
for rel in ["schema/examples/explain.inputs.json", "schema/examples/summary.inputs.json", "schema/examples/scenario-name.inputs.json"]:
    for e in load(rel)["examples"]:
        chk = e["sampleCheck"]
        flat = chk.values() if "pass" not in chk else [chk]
        ok(all(x["pass"] for x in flat), f"{rel} {e.get('name', '')} {chk}")

# 5. 공통 응답 형태 (API 공통 규칙)
import re  # noqa: E402
for e in load("schema/examples/api-responses.json")["examples"]:
    r, n = e["response"], e["name"]
    ok(set(r) == {"isSuccess", "code", "message", "result"}, f"{n} envelope keys")
    ok(isinstance(r["message"], str) and r["message"], f"{n} message")
    if r["isSuccess"]:
        ok(re.fullmatch(r"[A-Z]+2\d\d_\d+", r["code"]) is not None, f"{n} success code {r['code']}")
    else:
        ok(re.fullmatch(r"[A-Z]+[45]\d\d_\d+", r["code"]) is not None, f"{n} error code {r['code']}")
        ok(r["result"] is None, f"{n} error result must be null")
    res = r["result"] or {}
    if res.get("type") == "change":
        ok(not S.validate_condition(res["newCondition"]), f"{n} newCondition valid")
        if res["answerText"]:
            ok(V.check(res["answerText"].replace(" 이자·세금은 반영하지 않았어요.", ""), "change.answerText",
                       V.allowed_from_input(load("schema/examples/explain.inputs.json")["examples"][0]["input"]))["pass"], f"{n} answerText")

# 6. 검증 에러: 필드별 코드, 첫 번째 하나만
for c in load("tests/condition.errors.json")["cases"]:
    got = S.first_condition_error(c["condition"])
    ok((got["code"] if got else None) == c["expect"], f"condition error {c['name']}: {got}")

print("ALL PASS" if not fails else f"{fails} FAIL")
sys.exit(1 if fails else 0)
