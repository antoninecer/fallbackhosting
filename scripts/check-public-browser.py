#!/usr/bin/env python3
"""Optional Playwright QA of the public page. Screenshots stay in ignored .local/qa."""
import json
from pathlib import Path
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
output = ROOT / '.local/qa' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
output.mkdir(parents=True, exist_ok=True)
results = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in (360, 768, 1440):
        page = browser.new_page(viewport={'width':width, 'height':900}, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        response = page.goto('https://project.lab.ventureout.cz/', wait_until='networkidle')
        assert response.status == 200
        assert page.locator('html').get_attribute('lang') == 'cs'
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Page overflow at {width}'
        panel = page.locator('.progress-log')
        assert panel.get_attribute('tabindex') == '0'
        assert panel.evaluate('(e) => e.scrollHeight > e.clientHeight'), 'History must overflow inside panel'
        height = panel.evaluate('(e) => e.getBoundingClientRect().height')
        assert height < 620, 'History not bounded'
        panel.focus()
        assert panel.evaluate('(e) => document.activeElement === e')
        page.keyboard.press('PageDown')
        page.wait_for_timeout(350)
        assert panel.evaluate('(e) => e.scrollTop > 0'), 'Keyboard scrolling failed'
        before = page.locator('#milniky').evaluate('(e) => e.getBoundingClientRect().top + scrollY')
        panel.locator('ol').evaluate('(e) => { for(let i=0;i<40;i++) e.append(e.firstElementChild.cloneNode(true)); }')
        after = page.locator('#milniky').evaluate('(e) => e.getBoundingClientRect().top + scrollY')
        assert abs(after-before) <= 1, 'Growing history moves later page sections'
        panel.evaluate('(e) => e.scrollTop = 0')
        select = page.locator('#task-filter')
        for option in ('DONE', 'ACTIVE', 'BLOCKED', 'READY', 'ALL'):
            select.select_option(option)
            actual = page.locator('tbody tr[data-status]:visible').count()
            expected = page.locator('tbody tr[data-status]').evaluate_all('''(rows, option) => rows.filter(row => option === 'ALL' || row.dataset.status === option || (option === 'ACTIVE' && ['IN_PROGRESS','TESTING'].includes(row.dataset.status))).length''', option)
            assert actual == expected, f'Filter {option} at {width}'
            assert page.locator('#filter-result').inner_text()
        assert not errors, 'Browser JavaScript errors'
        page.screenshot(path=str(output / f'public-{width}.png'), full_page=True)
        results.append({'width':width, 'status':'PASS', 'panel_height_px':height, 'history_growth_page_shift_px':after-before, 'javascript_errors':len(errors)})
        page.close()
    browser.close()
report = {'verified_at_utc':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'url':'https://project.lab.ventureout.cz/', 'checks':results}
(output / 'public-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
print('Screenshots/report stored privately in',output.relative_to(ROOT))
