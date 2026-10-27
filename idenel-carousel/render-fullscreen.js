// Renders fullscreen.html (?lang=ru|uz) to five 9:16 cards per language at 2x (2160x3840)
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
(async () => {
  const b = await chromium.launch();
  for (const lang of ['ru', 'uz']) {
    const out = path.join(__dirname, 'export', 'fullscreen-9x16', lang); fs.mkdirSync(out, { recursive: true });
    const p = await b.newPage({ viewport: { width: 1200, height: 2000 }, deviceScaleFactor: 2 });
    await p.goto('file://' + path.join(__dirname, 'fullscreen.html') + '?lang=' + lang, { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    const s = await p.$$('.slide');
    for (let i = 0; i < s.length; i++) {
      await s[i].screenshot({ path: `${out}/idenel-${lang}-${i + 1}.png` });
      await s[i].screenshot({ path: `${out}/idenel-${lang}-${i + 1}.jpg`, type: 'jpeg', quality: 100 });
    }
    await p.close();
  }
  await b.close(); console.log('done');
})();
