const { chromium } = require('playwright');

(async () => {
  const sizes = [
    { w: 320, h: 720 },
    { w: 375, h: 812 },
  ];
  const browser = await chromium.launch({ headless: true });

  for (const s of sizes) {
    const context = await browser.newContext({ viewport: { width: s.w, height: s.h } });
    const page = await context.newPage();
    await page.goto('http://127.0.0.1:4173/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(800);

    const data = await page.evaluate(() => {
      const vw = window.innerWidth;
      const doc = document.documentElement;
      const body = document.body;
      const base = {
        vw,
        docScrollW: doc.scrollWidth,
        bodyScrollW: body ? body.scrollWidth : null,
        docClientW: doc.clientWidth,
        bodyClientW: body ? body.clientWidth : null,
      };

      const nodes = Array.from(document.querySelectorAll('*'));
      const wide = nodes
        .map((el) => {
          const sw = el.scrollWidth;
          const cw = el.clientWidth;
          return {
            tag: el.tagName.toLowerCase(),
            id: el.id || '',
            cls: (el.className || '').toString().trim().slice(0, 120),
            sw,
            cw,
            delta: sw - cw,
          };
        })
        .filter((x) => x.delta > 20 || x.sw > vw + 20)
        .sort((a, b) => (b.sw - b.cw) - (a.sw - a.cw))
        .slice(0, 30);

      return { base, wide };
    });

    console.log(`\n=== ${s.w}x${s.h} ===`);
    console.log(data.base);
    console.log(data.wide);

    await context.close();
  }

  await browser.close();
})();
