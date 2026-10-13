"""Download the web fonts the page uses (latin + latin-ext) into assets/fonts/ for the website build.

Usage: python -I fetch_fonts.py
Writes assets/fonts/*.woff2 and assets/fonts/fonts.css (@font-face rules pointing at /fonts/).
build_page.py copies them to site/public/fonts/ and inlines fonts.css in the site page.
The claude.ai artifact build keeps the Google Fonts link. All three families are under the SIL Open Font License 1.1.
"""
import os
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "fonts")
CSS_URL = ("https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900"
           "&family=Atkinson+Hyperlegible+Mono:wght@400..700"
           "&family=Atkinson+Hyperlegible+Next:ital,wght@0,200..800;1,200..800&display=swap")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"
KEEP = {"latin", "latin-ext"}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read()


def main():
    os.makedirs(OUT, exist_ok=True)
    css = get(CSS_URL).decode()
    rules = []
    for subset, body in re.findall(r"/\* ([a-z-]+) \*/\s*@font-face \{(.*?)\}", css, re.S):
        if subset not in KEEP:
            continue
        family = re.search(r"font-family: '([^']+)'", body).group(1)
        style = re.search(r"font-style: (\w+)", body).group(1)
        url = re.search(r"src: url\((https://[^)]+\.woff2)\)", body).group(1)
        name = f"{family.lower().replace(' ', '-')}-{style}-{subset}.woff2"
        with open(os.path.join(OUT, name), "wb") as f:
            f.write(get(url))
        local = re.sub(r"src: url\([^)]+\)", f"src: url(/fonts/{name})", body.strip())
        rules.append(f"/* {subset} */\n@font-face {{\n  {local}\n}}")
        print("saved", name)
    with open(os.path.join(OUT, "fonts.css"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(rules) + "\n")
    print(f"wrote {len(rules)} @font-face rules")


if __name__ == "__main__":
    main()
