// Renders story-ru.html to one 1080x1920 (9:16) PNG + JPG for Stories/Reels ads
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
(async () => {
  const out = path.join(__dirname, 'export', 'story'); fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file://' + path.join(__dirname, 'story-ru.html'), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  const el = await p.$('#story');
  await el.screenshot({ path: `${out}/idenel-seminar-story-ru-1080x1920.png` });
  await el.screenshot({ path: `${out}/idenel-seminar-story-ru-1080x1920.jpg`, type: 'jpeg', quality: 95 });
  await b.close(); console.log('done');
})();
