import requests
import os
import sys


def load_env():
    if not os.path.exists(".env"):
        return
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def get_articles(api_key, keyword=None, source=None, from_date=None, to_date=None):
    url = "https://newsapi.org/v2/everything"

    params = {
        "apiKey": api_key,
        "q": keyword or "latest",
        "sources": source or "wired",
        "from": from_date,
        "to": to_date,
        "sortBy": "publishedAt",
        "pageSize": 10,
    }
    params = {k: v for k, v in params.items() if v is not None}

    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Could not connect. Check your internet connection.")
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out.")

    ERROR_MESSAGES = {
        400: "Error 400. Bad request. Check your parameters (source name, date format, etc.).",
        401: "Error 401. Invalid API key. Check NEWS_API_KEY in your .env file.",
        426: "Error 426. Free API key only supports articles from the last 30 days. Use a more recent date range.",
        429: "Error 429. Rate limit exceeded. Please wait before retrying.",
        500: "Error 500. NewsAPI server error. Try again later.",
    }

    if response.status_code in ERROR_MESSAGES:
        raise RuntimeError(ERROR_MESSAGES[response.status_code])
    if response.status_code != 200:
        raise RuntimeError(f"NewsAPI error (HTTP {response.status_code}).")

    data = response.json()
    # if data.get("status") != "ok":
    #     raise RuntimeError(f"NewsAPI error: {data.get('message', 'Unknown error')}")

    return data.get("articles", [])


def summarize(articles):
    for art in articles:
        print("Title:", art.get('title') or 'No title')
        print("Description:", art.get('description') or 'No description')
        print("URL:", art.get('url') or 'N/A')
        print("----")


def parse_args():
    args = {}
    argv = sys.argv[1:]
    for i in range(0, len(argv) - 1, 2):
        flag = argv[i].lstrip("-")  # e.g. "--keyword" -> "keyword"
        args[flag] = argv[i + 1]
    return args

load_env()

api_key = os.environ.get("NEWS_API_KEY")
if not api_key:
    print("Error: NEWS_API_KEY not set. Add it to a .env file:\n  NEWS_API_KEY=your_key_here")
    sys.exit(1)

args = parse_args()

try:
    articles = get_articles(
        api_key,
        keyword=args.get("keyword"),
        source=args.get("source"),
        from_date=args.get("from"),
        to_date=args.get("to"),
    )
except RuntimeError as e:
    print(f"Error: {e}")
    sys.exit(1)

if not articles:
    print("No articles found.")
else:
    print(f"Found {len(articles)} article(s):\n")
    summarize(articles)