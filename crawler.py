import requests

# 검색어 입력
search = input("검색어를 입력하세요: ")

# 제외할 사이트 목록
excluded_sites = "-site:blog.naver.com -site:namu.wiki -site:ko.wikipedia.org"
query = f"{search} {excluded_sites}"

# Serper API 설정
API_KEY = "d106b73697445f7be8dcac3f1216be25a3c246ce"
url = "https://google.serper.dev/search"

headers = {
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

data = {
    "q": query,
    "hl": "ko"  # 한국어 검색 결과
}

# 요청 보내기
res = requests.post(url, headers=headers, json=data)

# 결과 처리
if res.status_code == 200:
    results = res.json()
    # 첫 번째 웹 링크 가져오기
    if results.get("organic") and len(results["organic"]) > 0:
        first = results["organic"][0]
        print(f"\n[🔗 가장 상단 링크] {first['link']}")
        print(f"[📝 제목] {first['title']}")
        print(f"[📄 요약] {first['snippet']}")
    else:
        print("검색 결과가 없습니다.")
else:
    print("API 요청 실패:", res.status_code)
