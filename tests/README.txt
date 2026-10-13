Browser tests (Playwright). Setup: npm install playwright-core, install a Chromium build (set CHROMIUM_PATH if it is not the default), run python -I build_page.py, then run each file with node, for example: node tests/smoke.js
Screenshots and PDFs go to tests/.tmp (or the folder in the TEST_TMP environment variable).
site_check.js takes the site URL as its argument and submits one anonymous test answer.
