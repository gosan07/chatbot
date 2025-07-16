from flask import Flask, render_template, request, jsonify
import requests
import json

app = Flask(__name__)

# data.json에서 데이터 로드
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

API_KEY = "d106b73697445f7be8dcac3f1216be25a3c246ce"
SERPER_URL = "https://google.serper.dev/search"
EXCLUDED_SITES = "-site:blog.naver.com -site:namu.wiki -site:ko.wikipedia.org"
import re

def normalize(text):
    return re.sub(r"\s+", "", text.lower())
def search_places_by_keyword(query):
    results = []
    norm_query = normalize(query)
    print("정규화된 사용자 입력:", norm_query)

    for item in data:
        place = item.get("place", "")
        events = item.get("event", [])
        keywords = item.get("keywords", [])

        if isinstance(events, str):
            events = [events]
        if isinstance(keywords, str):
            keywords = [keywords]

        norm_place = normalize(place)
        norm_events = [normalize(e) for e in events]
        norm_keywords = [normalize(k) for k in keywords]

        match_place = norm_place in norm_query or norm_query in norm_place
        match_event = any(e in norm_query or norm_query in e for e in norm_events)
        match_keyword = any(k in norm_query or norm_query in k for k in norm_keywords)

        # 🔍 디버깅 출력
        print(f"[검사] {place} → place match: {match_place}, event match: {match_event}, keyword match: {match_keyword}")

        if match_place or match_event or match_keyword:
            results.append(item)

    return results


def serper_search(query):
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    search_query = f"{query} {EXCLUDED_SITES}"
    payload = {"q": search_query, "hl": "ko"}
    res = requests.post(SERPER_URL, headers=headers, json=payload)
    if res.status_code == 200:
        result = res.json()
        if result.get("organic"):
            first = result["organic"][0]
            return {
                "link": first.get("link"),
                "title": first.get("title"),
                "snippet": first.get("snippet")
            }
    return None

@app.route("/")
def index():
    return render_template("index.html")

def find_exact_place_and_context(query):
    norm_query = normalize(query)
    matched_place = None
    matched_events = []
    matched_keywords = []

    for item in data:
        norm_place = normalize(item.get("place", ""))
        events = item.get("event", [])
        keywords = item.get("keywords", [])

        if isinstance(events, str): events = [events]
        if isinstance(keywords, str): keywords = [keywords]

        norm_events = [normalize(e) for e in events]
        norm_keywords = [normalize(k) for k in keywords]

        # 장소 이름이 들어 있으면 우선 선택
        if norm_place in norm_query or norm_query in norm_place:
            matched_place = item

        # 항목 단위로 이벤트/키워드도 추적
        if any(e in norm_query or norm_query in e for e in norm_events):
            matched_events.extend(events)
        if any(k in norm_query or norm_query in k for k in norm_keywords):
            matched_keywords.extend(keywords)

    return matched_place, list(set(matched_events)), list(set(matched_keywords))
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    response = ""

    # 1. 입장료 질문 먼저 처리
    if "입장료" in user_message or "요금" in user_message:
        place, _, _ = find_exact_place_and_context(user_message)
        fee_types = ["성인", "어린이", "청소년", "군인", "성인 단체", "어린이 단체", "청소년 단체", "군인 단체"]

        if place:
            response += f"'{place['place']}'의 입장료는 다음과 같습니다:\n"
            entry_type = place.get("entry_type", [])
            entry_fee = place.get("entry_fee", [])
            if isinstance(entry_type, str): entry_type = [entry_type]
            if isinstance(entry_fee, str): entry_fee = [entry_fee]

            found = False
            for i, fee_type in enumerate(fee_types):
                if fee_type in user_message:
                    if i < len(entry_type) and i < len(entry_fee):
                        response += f"- {entry_type[i]}: {entry_fee[i]}\n"
                        found = True
                        break
            if not found:
                for etype, fee in zip(entry_type, entry_fee):
                    response += f"- {etype}: {fee}\n"
        else:
            response += "입장료 정보를 제공할 수 있는 장소를 찾지 못했습니다."
        return jsonify({"answer": response})

    # 2. 일반적인 장소/사건/키워드 질문 처리
    place, events, keywords = find_exact_place_and_context(user_message)

    if place:
        response += f"'{place['place']}'에 대해 안내드리겠습니다.\n"
        response += f"- 위치: {place['address']}\n"
        response += f"- 개요: {place['description']}\n"
        if any(e in place.get("event", []) for e in events):
            response += f"- '{', '.join(events)}'과(와) 관련된 역사적 의미: {place['historical_relevance']}\n"
        else:
            response += f"- 역사적 배경: {place['historical_relevance']}\n"
    elif events or keywords:
        results = search_places_by_keyword(user_message)
        if results:
            response += "관련된 장소는 다음과 같습니다:\n\n"
            for item in results[:3]:
                response += f"📍 {item['place']} - {item['address']}\n"
        else:
            response += "해당 주제와 관련된 장소를 찾을 수 없습니다.\n"
    else:
        response += "질문에 해당하는 장소나 사건을 찾지 못했습니다. 다른 표현으로 다시 질문해 주세요.\n"

    return jsonify({"answer": response})


if __name__ == "__main__":
    app.run(debug=True)
