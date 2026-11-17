"""1단계 해석 프롬프트 자동 시험: tests/questions.json 30개를 Gemini API로 하나씩 호출하고 채점한다.

질문마다 새 요청을 보내므로(대화 기록 없음) 실제 서비스와 같은 조건이다.
표준 라이브러리만 쓴다. 설치할 것 없음.

준비
  1. AI Studio 왼쪽 아래 열쇠 아이콘(Get API key)에서 API 키를 만든다.
  2. 키를 환경 변수로 넣는다. 키는 파일이나 Git에 적지 않는다.
       PowerShell:  $env:GEMINI_API_KEY="발급받은키"
       cmd:         set GEMINI_API_KEY=발급받은키
실행 (WhatIf_v0 폴더에서)
  python tests/run_gemini_eval.py                    # 30개 전체
  python tests/run_gemini_eval.py --ids 1 2 4 25     # 일부만
  python tests/run_gemini_eval.py --dry-run          # 키 없이 채점 로직만 확인
옵션
  --model gemini-4-hydrogen   AI Studio에서 쓰는 모델 ID
  --thinking low              thinkingLevel. 모델이 거부하면 --thinking none
  --temperature 0             모델이 거부하면 생략
  --sleep 1                   요청 사이 대기(초). 429가 나면 늘린다
결과
  tests/results/interpret-<날짜시각>.json  질문별 출력·채점·시간
  화면에 요약(유형 정확도, 출력 정확도, 평균·최대 시간, 틀린 질문 목록)
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = "2026-11-16"  # 정답지 날짜 기준. 실제 오늘 날짜로 바꾸면 날짜 문제 정답이 달라진다
API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f) if rel.endswith(".json") else f.read()


def strip_nulls(o):
    """null 필드와 빈 값을 지워서 비교한다 (Gemini는 null 필드를 생략하기도 한다)."""
    if isinstance(o, dict):
        return {k: strip_nulls(v) for k, v in o.items() if v is not None}
    if isinstance(o, list):
        return [strip_nulls(x) for x in o]
    return o


def build_input(q, fixtures):
    f = fixtures[q["fixture"]]
    return {"today": TODAY, "question": q["question"], "baseVersionNo": f["baseVersionNo"],
            "nextVersionNo": f["nextVersionNo"], "versions": f["versions"]}


def call_gemini(args, system, schema, user_json, key):
    gen = {"responseMimeType": "application/json", "responseSchema": schema}
    if args.temperature is not None:
        gen["temperature"] = args.temperature
    if args.thinking != "none":
        gen["thinkingConfig"] = {"thinkingLevel": args.thinking}
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": json.dumps(user_json, ensure_ascii=False)}]}],
            "generationConfig": gen}
    req = urllib.request.Request(API.format(model=args.model), data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": key}, method="POST")
    with urllib.request.urlopen(req, timeout=args.timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    text = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"] if not p.get("thought"))
    return json.loads(text)


def grade(q, out):
    type_ok = isinstance(out, dict) and out.get("type") == q["expectedType"]
    if q["expected"] is None:
        return type_ok, type_ok
    goods = [q["expected"]] + q.get("alternatives", [])
    return type_ok, any(strip_nulls(out) == strip_nulls(g) for g in goods)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemini-4-hydrogen")
    ap.add_argument("--thinking", default="low", help="low | medium | high | none")
    ap.add_argument("--temperature", type=float, default=None)
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--timeout", type=float, default=60)
    ap.add_argument("--ids", type=int, nargs="*")
    ap.add_argument("--dry-run", action="store_true", help="API 대신 정답을 출력으로 써서 채점 흐름만 확인")
    args = ap.parse_args()

    key = os.environ.get("GEMINI_API_KEY")
    if not key and not args.dry_run:
        sys.exit("GEMINI_API_KEY 환경 변수가 없어요. 파일 맨 위 '준비'를 보세요.")

    system = load("prompts/interpret.system.txt")
    schema = load("schema/gemini/interpret.response-schema.json")
    fixtures = load("schema/fixtures/chat-requests.json")["fixtures"]
    questions = load("tests/questions.json")["questions"]
    if args.ids:
        questions = [q for q in questions if q["id"] in set(args.ids)]

    rows = []
    for q in questions:
        user_json = build_input(q, fixtures)
        t0 = time.perf_counter()
        err, out = None, None
        try:
            out = (q["expected"] or {"type": q["expectedType"]}) if args.dry_run else call_gemini(args, system, schema, user_json, key)
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}"
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {e}"
        sec = round(time.perf_counter() - t0, 2)
        type_ok, out_ok = (False, False) if err else grade(q, out)
        rows.append({"id": q["id"], "question": q["question"], "expectedType": q["expectedType"],
                     "typeOk": type_ok, "outputOk": out_ok, "seconds": sec, "output": out, "error": err,
                     "expected": q["expected"], "note": q["note"]})
        mark = "OK " if out_ok else ("TYP" if type_ok else "XX ")
        print(f"[{mark}] #{q['id']:>2} {sec:>5}s  {q['question']}" + (f"  !! {err}" if err else ""))
        if not args.dry_run:
            time.sleep(args.sleep)

    n = len(rows)
    secs = [r["seconds"] for r in rows if not r["error"]]
    summary = {
        "model": args.model, "thinking": args.thinking, "temperature": args.temperature, "dryRun": args.dry_run,
        "count": n,
        "typeAccuracy": f"{sum(r['typeOk'] for r in rows)}/{n}",
        "outputAccuracy": f"{sum(r['outputOk'] for r in rows)}/{n}",
        "avgSeconds": round(sum(secs) / len(secs), 2) if secs else None,
        "maxSeconds": max(secs) if secs else None,
        "errors": sum(1 for r in rows if r["error"]),
        "wrong": [r["id"] for r in rows if not r["outputOk"]],
    }
    os.makedirs(os.path.join(ROOT, "tests", "results"), exist_ok=True)
    name = f"interpret-{datetime.now():%Y%m%d-%H%M}{'-dry' if args.dry_run else ''}.json"
    path = os.path.join(ROOT, "tests", "results", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": rows}, f, ensure_ascii=False, indent=2)
    print("\n" + json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n결과 파일: {path}")


if __name__ == "__main__":
    main()
