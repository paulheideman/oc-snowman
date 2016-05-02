from __future__ import print_function
from bs4 import BeautifulSoup
import requests, requests.exceptions, re, os, os.path, gzip, time, random


ai_re = re.compile(r"^/ai/([a-z0-9]{8})")
def ai_id(s):
    rs = ai_re.search(s)
    return rs is not None and rs.group(1) or None


def ai_url(s):
    return s.startswith("/ai/")


game_re = re.compile(r"^/([a-z0-9]{8})")
def game_id(s):
    rs = game_re.search(s)
    return rs is not None and rs.group(1) or None


def game_url(s):
    if s.startswith("/register") or s.startswith("/starters"):
        return False
    else:
        return game_id(s) is not None


def get_request(s, url):
    success = False
    delay = 1.0
    r = None
    while not success:
        try:
            r = s.get(url)
            success = True
        except requests.exceptions.RequestException, e:
            time.sleep(delay)
            delay = delay * random.uniform(1.0, 3.0)
            if delay > 30.0:
                delay = 30.0
    return r


def game_filename(id):
    return os.path.join("games", id)


def get_event_stream(s, next):
    if game_url(next):
        id = game_id(next)
        fn = game_filename(id)
        if not os.path.exists(fn):
            print(id, "new")
            r = get_request(s, base_url + "/events/" + id)
            if r.status_code == 200:
                with gzip.open(fn, "wb") as f:
                    f.write(unicode(r.text).encode('utf-8'))
            else:
                print("Failed: " + id)
                print(r.text)


def all_ai():
    r = []
    for id in os.listdir("ai"):
        r.append("/ai/" + id)
    return r


def ai_filename(id):
    return os.path.join("ai", id)


def exists_ai(id):
    return os.path.exists(ai_filename(id))


def record_ai(id):
    fn = ai_filename(id)
    with open(fn, 'a'):
        os.utime(fn, None)


if __name__ == "__main__":
    base_url = "http://vindinium.org"
    urls = set(["/", "/ai"]).union(all_ai())
    searched = set()
    s = requests.Session()
    while len(urls) > 0:
        next = urls.pop()
        print(next)
        fetch_url = base_url + next
        r = get_request(s, fetch_url)
        if r.status_code == 200:
            get_event_stream(s, next)
            soup = BeautifulSoup(r.text, "html.parser")
            for link in soup.find_all("a"):
                url = link["href"]
                interesting = False
                if ai_url(url):
                    interesting = True
                elif game_url(url):
                    id = game_id(url)
                    fn = game_filename(id)
                    if not os.path.exists(fn):
                        interesting = True
                if interesting:
                    if not url in searched and not url in urls:
                        urls.add(url)
        time.sleep(random.uniform(1.0, 3.0))
        if ai_url(next):
            id = ai_id(next)
            record_ai(id)
        searched.add(next)
