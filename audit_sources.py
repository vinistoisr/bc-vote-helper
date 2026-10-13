"""Source trust check for quiz_spec.json. Run after build_spec.py, before build_page.py.

Usage:
    python -I audit_sources.py            # tier check only (fast, offline)
    python -I audit_sources.py --links    # also fetch every URL and report dead links

Tiers (the policy is in README.md, "How sources are chosen"):
  T1  primary: the party or candidate's own pages, government, Legislature, Elections BC, statutes, StatCan,
      official poll releases
  T2  established news outlets with editors and a corrections policy
  T3  aggregators, Wikipedia, opinion, advocacy, partisan outlets, social posts: may be listed as extra
      reading, never as the only support for a party position, a candidate bio or a voting rule

Fails (exit 1) when a party position, candidate bio, party profile or voting rule has no T1/T2 source,
or when a source's domain is not classified yet (add it to a tier list below after checking the outlet).
"""
import concurrent.futures
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

T1 = """
bcndp.ca conservativebc.ca bcgreens.ca centrebc.ca 1bc.ca
gov.bc.ca news.gov.bc.ca archive.news.gov.bc.ca bcbudget.gov.bc.ca surreylangleyskytrain.gov.bc.ca
leg.bc.ca lims.leg.bc.ca bclaws.gov.bc.ca elections.bc.ca votebymail.elections.bc.ca
statcan.gc.ca www150.statcan.gc.ca canada.ca cmhc-schl.gc.ca
surrey.ca surreypolice.ca ubcm.ca bccsu.ca bccdc.ca fraserhealth.ca
ipsos.com angusreid.org legermarketing.com
""".split()

T2 = """
cbc.ca amp.cbc.ca ctvnews.ca guelph.ctvnews.ca globalnews.ca cp24.com bnnbloomberg.ca ca.news.yahoo.com
nationalnewswatch.com boereport.com vancouversun.com theprovince.com timescolonist.com thetyee.ca thenarwhal.ca
biv.com dailyhive.com storeys.com cheknews.ca
surreynowleader.com langleyadvancetimes.com nanaimobulletin.com kelownacapnews.com abbynews.com interior-news.com
theprogress.com wltribune.com thenorthernview.com agassizharrisonobserver.com cranbrooktownsman.com aldergrovestar.com
mapleridgenews.com vernonmorningstar.com pentictonwesternnews.com cloverdalereporter.com boundarycreektimes.com
missioncityrecord.com pqbnews.com revelstokereview.com nelsonstar.com trailtimes.ca ominecaexpress.com
caledoniacourier.com summerlandreview.com saobserver.net 100milefreepress.net thefreepress.ca
castanet.net castanetkamloops.net cfjctoday.com ckpgtoday.ca energeticcity.ca similkameenspotlight.com
sitkamedia.ca fraservalleytoday.ca mykootenaynow.com nanaimonewsnow.com mysouthokanagannow.com mynelsonnow.com
todayinbc.com am1150.ca connectfm.ca cjdctv.com nsnews.com delta-optimist.com prpeak.com piquenewsmagazine.com
therockymountaingoat.com voiceonline.com fvcurrent.com medicinehatnews.com westknews.com
mycariboonow.com peacearchnews.com vicnews.com narcity.com
""".split()

T3 = """
wikipedia.org en.wikipedia.org upload.wikimedia.org bcballot.ca bcelectionguide.ca votemate.org poliwave.com 338canada.com
x.com twitter.com facebook.com instagram.com youtube.com youtu.be stephentaylor.ca armchairmayor.ca westernstandard.news
fraserinstitute.org sogieducation.org bcnu.org fnlc.ca blakes.com blg.com treefrogcreative.ca swrbot.com
victoriabuzz.com ufvcascade.ca bbot.ca
""".split()

# Official party accounts (as linked from the party's own website) count as primary (T1); every other
# social post is T3, including leaders' personal accounts until checked.
# YouTube videos are listed one by one after checking the channel (youtube.com/oembed?url=... gives author_url).
OFFICIAL_SOCIAL = """
x.com/One_BCHQ x.com/VoteCentreBC x.com/bcgreens x.com/bcndp
youtube.com/watch?v=WQk8R4dwmsI
""".split()

URL_RE = re.compile(r"https?://[^\s;,\"'<>]+")


def tier(url):
    host = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    bare = re.sub(r"^https?://(www\.)?", "", url).replace("twitter.com/", "x.com/").lower()
    if any(bare == a.lower() or bare.startswith(a.lower() + "/") or bare.startswith(a.lower() + "&") for a in OFFICIAL_SOCIAL):
        return "T1"
    for name, doms in (("T1", T1), ("T2", T2), ("T3", T3)):
        if any(host == d or host.endswith("." + d) for d in doms):
            return name
    return "?"


def clean(u):
    """Trim trailing punctuation, but keep a ')' that closes a '(' inside the URL (Wikipedia titles)."""
    u = u.rstrip(".,")
    while u.endswith(")") and u.count(")") > u.count("("):
        u = u[:-1].rstrip(".,")
    return u


def urls_of(sources):
    out = []
    for s in sources or []:
        u = s.get("url") if isinstance(s, dict) else s
        if isinstance(u, str):
            out += URL_RE.findall(u) or [u]
    return [clean(u) for u in out]


def holders(spec):
    """(where, [urls]) for every item that must carry at least one T1/T2 source."""
    for q in spec["questions"]:
        for p, pos in q.get("party_positions", {}).items():
            if pos.get("no_position") and not pos.get("sources"):
                continue
            yield f"question {q['id']} / {p}", urls_of(pos.get("sources"))
    for p in spec["parties"]:
        yield f"party {p['id']}", urls_of(p.get("sources"))
    for r in spec["ridings"]:
        for grp in ("candidates", "others"):
            for c in r.get(grp, []):
                if c.get("bio"):
                    yield f"riding {r['name']} / {c['name']}", urls_of(c.get("sources"))
    for c in spec["local"].get("candidates", []):
        yield f"local {c['name']}", urls_of(c.get("sources"))


def all_urls(spec):
    found = set()

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str):
            found.update(clean(u) for u in URL_RE.findall(o))

    walk(spec)
    return sorted(found)


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def fetch_status(url):
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
            return url, urllib.request.urlopen(req, timeout=25).status
        except urllib.error.HTTPError as e:
            if method == "GET":
                return url, e.code
        except Exception as e:  # noqa: BLE001 - any network failure is a result here
            if method == "GET":
                return url, type(e).__name__


def main():
    spec = json.load(open(os.path.join(HERE, "quiz_spec.json"), encoding="utf-8"))
    urls = all_urls(spec)
    counts = {"T1": 0, "T2": 0, "T3": 0, "?": 0}
    for u in urls:
        counts[tier(u)] += 1
    print(f"{len(urls)} unique URLs: T1 {counts['T1']}, T2 {counts['T2']}, T3 {counts['T3']}, unclassified {counts['?']}")

    problems = 0
    unknown = sorted({urllib.parse.urlparse(u).netloc for u in urls if tier(u) == "?"})
    if unknown:
        problems += len(unknown)
        print("\nUnclassified domains (check the outlet, then add it to T1, T2 or T3 in audit_sources.py):")
        for d in unknown:
            print("  " + d)

    weak = [(w, us) for w, us in holders(spec) if not any(tier(u) in ("T1", "T2") for u in us)]
    if weak:
        problems += len(weak)
        print(f"\n{len(weak)} items with no T1/T2 source:")
        for w, us in weak:
            print(f"  {w}: {', '.join(us) or 'no sources'}")

    rules = re.compile(r"advance|mail-in|eligib|voter id|ID rules|registration", re.I)
    htv = urls_of(s for s in spec.get("sources", []) if rules.search(s.get("used_for") or ""))
    if htv and not all(tier(u) == "T1" for u in htv):
        problems += 1
        print("\nVoting-rule sources must all be Elections BC (T1):", [u for u in htv if tier(u) != "T1"])

    if "--links" in sys.argv:
        with concurrent.futures.ThreadPoolExecutor(24) as ex:
            res = list(ex.map(fetch_status, urls))
        dead = [(u, s) for u, s in res if s in (404, 410)]
        other = [(u, s) for u, s in res if s != 200 and (u, s) not in dead]
        print(f"\nLinks: {len(res) - len(dead) - len(other)} OK, {len(dead)} dead, {len(other)} blocked or flaky (403/429/5xx/timeout; check by hand)")
        for u, s in dead:
            print(f"  DEAD {s} {u}")
        for u, s in other:
            print(f"  ?    {s} {u}")
        problems += len(dead)

    print("\nsource check:", "PASS" if not problems else f"FAIL ({problems} problems)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
