// Renders single-ru.html to one 1080x1080 PNG + JPG
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
(async () => {
  const out = path.join(__dirname, 'export', 'single'); fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1080 } });
  await p.goto('file://' + path.join(__dirname, 'single-ru.html'), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  const el = await p.$('#single');
  await el.screenshot({ path: `${out}/idenel-seminar-ru-1080.png` });
  await el.screenshot({ path: `${out}/idenel-seminar-ru-1080.jpg`, type: 'jpeg', quality: 95 });
  await b.close(); console.log('done');
})();
