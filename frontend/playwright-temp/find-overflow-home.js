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

    const offenders = await page.evaluate(() => {
      const vw = window.innerWidth;
      const nodes = Array.from(document.querySelectorAll('*'));
      return nodes
        .map((el) => {
          const r = el.getBoundingClientRect();
          const cs = getComputedStyle(el);
          return {
            tag: el.tagName.toLowerCase(),
            cls: (el.className || '').toString().trim().slice(0, 120),
            id: el.id || '',
            left: Math.round(r.left),
            right: Math.round(r.right),
            width: Math.round(r.width),
            overflowX: cs.overflowX,
          };
        })
        .filter((x) => x.right > vw + 1 || x.left < -1)
        .sort((a, b) => b.right - a.right)
        .slice(0, 20);
    });

    console.log(`\n=== ${s.w}x${s.h} ===`);
    console.log(offenders);

    await context.close();
  }

  await browser.close();
})();
