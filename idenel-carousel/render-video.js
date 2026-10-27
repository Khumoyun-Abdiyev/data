// Renders video.html (?lang=uz|ru) to a 1080x1920 30fps H.264 MP4 by scrubbing paused CSS animations frame by frame
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
const { execFileSync } = require('child_process');
const FPS = 30;
(async () => {
  const langs = process.argv.slice(2).length ? process.argv.slice(2) : ['uz', 'ru'];
  const b = await chromium.launch();
  for (const lang of langs) {
    const tmp = path.join(__dirname, 'export', 'video', `frames-${lang}`); fs.mkdirSync(tmp, { recursive: true });
    const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
    await p.goto('file://' + path.join(__dirname, 'video.html') + '?lang=' + lang, { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    const dur = await p.evaluate(() => window.DURATION);
    const stage = await p.$('#stage');
    for (let f = 0; f < dur * FPS; f++) {
      await p.evaluate(ms => document.getAnimations().forEach(a => a.currentTime = ms), (f / FPS) * 1000);
      await stage.screenshot({ path: `${tmp}/f${String(f).padStart(4, '0')}.jpg`, type: 'jpeg', quality: 95 });
    }
    await p.close();
    const out = path.join(__dirname, 'export', 'video', `idenel-seminar-${lang}-9x16.mp4`);
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', `${tmp}/f%04d.jpg`,
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]);
    fs.rmSync(tmp, { recursive: true });
    console.log('wrote', out);
  }
  await b.close();
})();
