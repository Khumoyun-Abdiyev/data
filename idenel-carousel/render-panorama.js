// Renders the 5 cards as ONE seamless 5400x1080 panorama, then slices it into 5 squares
const { chromium } = require('playwright');
const path = require('path'); const fs = require('fs');
(async () => {
  const out = path.join(__dirname, 'export', 'panorama'); fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 5400, height: 1080 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.join(__dirname, 'carousel.html'), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.addStyleTag({ content: `
    body{padding:0;gap:0;background:none}
    #pano{position:relative;width:5400px;height:1080px;display:flex;overflow:hidden;
      background:
        radial-gradient(28% 70% at 8% 70%, #fff 0%, transparent 70%),
        radial-gradient(28% 70% at 30% 60%, #fff 0%, transparent 70%),
        radial-gradient(28% 70% at 52% 75%, #fff 0%, transparent 70%),
        radial-gradient(28% 70% at 72% 65%, #fff 0%, transparent 70%),
        radial-gradient(28% 70% at 94% 60%, #fff 0%, transparent 70%),
        linear-gradient(180deg,#F6F3EE,#ECE6DC)}
    #pano .card{background:transparent}
    #pano .card::after{display:none}
    #pano .foot{display:none}
    #pano .frame{position:absolute;left:36px;right:36px;top:36px;bottom:36px;border:1px solid rgba(169,132,76,.28);pointer-events:none}
    #pano .thread{position:absolute;left:0;top:0;width:5400px;height:1080px;pointer-events:none;z-index:1}
    #pano .swipe{position:absolute;bottom:62px;font-size:15px;font-weight:600;letter-spacing:.22em;color:#A9844C;z-index:6}
  `});
  await p.evaluate(() => {
    const pano = document.createElement('div'); pano.id = 'pano';
    document.querySelectorAll('.card').forEach(c => pano.appendChild(c));
    document.body.appendChild(pano);
    pano.insertAdjacentHTML('afterbegin', `
      <div class="frame"></div>
      <svg class="thread" viewBox="0 0 5400 1080" fill="none">
        <path d="M36 1004 C 700 1004, 900 960, 1300 975 S 2100 1020, 2500 990 S 3300 950, 3700 985 S 4600 1015, 5364 990"
              stroke="#CDB287" stroke-width="1.5"/>
        <path d="M36 1018 C 800 1020, 1000 985, 1400 995 S 2200 1030, 2600 1005 S 3400 975, 3800 1000 S 4700 1025, 5364 1008"
              stroke="#A9844C" stroke-width="1" opacity=".5"/>
      </svg>`);
    // small swipe cue "→" on cards 1-4, bottom right
    [1,2,3,4].forEach(i => pano.insertAdjacentHTML('beforeend',
      `<div class="swipe" style="left:${i*1080-150}px">→ →</div>`));
  });
  await (await p.$('#pano')).screenshot({ path: `${out}/idenel-seminar-panorama-5400x1080.png` });
  await b.close(); console.log('rendered');
})();
