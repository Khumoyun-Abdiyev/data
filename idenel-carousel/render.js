// Renders each .card in carousel.html to a 1080x1080 PNG + JPG in ./export
const { chromium } = require('playwright');
const path = require('path'); const fs = require('fs');
(async () => {
  const out = path.join(__dirname, 'export'); fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 1200 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.join(__dirname, 'carousel.html'), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  const names = ['01-cover', '02-microneedling', '03-home-care', '04-practice', '05-certificate-cta'];
  const cards = await p.$$('.card');
  for (let i = 0; i < cards.length; i++) {
    await cards[i].screenshot({ path: `${out}/idenel-seminar-${names[i]}.png` });
    await cards[i].screenshot({ path: `${out}/idenel-seminar-${names[i]}.jpg`, type: 'jpeg', quality: 95 });
  }
  await b.close(); console.log('done', cards.length);
})();
