// Renders feed.html (?lang=ru|uz) to five 1080x1350 PNG + JPG per language
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
(async () => {
  const b = await chromium.launch();
  for (const lang of ['ru', 'uz']) {
    const out = path.join(__dirname, 'export', 'feed-4x5', lang); fs.mkdirSync(out, { recursive: true });
    const p = await b.newPage({ viewport: { width: 1200, height: 1400 } });
    await p.goto('file://' + path.join(__dirname, 'feed.html') + '?lang=' + lang, { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    const s = await p.$$('.slide');
    for (let i = 0; i < s.length; i++) {
      await s[i].screenshot({ path: `${out}/idenel-${lang}-${i + 1}.png` });
      await s[i].screenshot({ path: `${out}/idenel-${lang}-${i + 1}.jpg`, type: 'jpeg', quality: 95 });
    }
    await p.close();
  }
  await b.close(); console.log('done');
})();
