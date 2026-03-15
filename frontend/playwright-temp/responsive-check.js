const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const base = 'http://127.0.0.1:4174';
  const viewports = [
    { name: '320', width: 320, height: 720 },
    { name: '375', width: 375, height: 812 },
    { name: '768', width: 768, height: 1024 },
    { name: '1024', width: 1024, height: 768 },
    { name: '1440', width: 1440, height: 900 },
  ];
  const routes = ['/', '/login', '/chat', '/catalogo', '/pago'];

  const outDir = path.resolve('playwright-temp', 'responsive-report');
  fs.mkdirSync(outDir, { recursive: true });
  const summaryPath = path.join(outDir, 'summary.tsv');
  const issuesPath = path.join(outDir, 'issues.tsv');
  fs.writeFileSync(summaryPath, 'route\tviewport\toverflowX\tstatus\n');
  fs.writeFileSync(issuesPath, 'route\tviewport\toverflowX\n');

  const browser = await chromium.launch({ headless: true });

  for (const vp of viewports) {
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
    const page = await context.newPage();

    for (const route of routes) {
      const url = `${base}${route}`;
      let overflowX = -1;
      let status = 'ok';
      try {
        await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 });
        await page.waitForTimeout(700);

        const metrics = await page.evaluate(() => {
          const doc = document.documentElement;
          const body = document.body;
          const scrollW = Math.max(doc.scrollWidth, body ? body.scrollWidth : 0);
          const innerW = window.innerWidth;
          const overflowX = Math.max(0, scrollW - innerW);
          return { overflowX, scrollW, innerW };
        });
        overflowX = metrics.overflowX;

        const routeName = route === '/' ? 'home' : route.replace(/\//g, '_').replace(/^_/, '');
        await page.screenshot({ path: path.join(outDir, `${routeName}-${vp.name}.png`), fullPage: true });

        if (overflowX > 1) {
          status = 'overflow';
          fs.appendFileSync(issuesPath, `${route}\t${vp.width}x${vp.height}\t${overflowX}\n`);
        }
      } catch (err) {
        status = 'error';
      }

      fs.appendFileSync(summaryPath, `${route}\t${vp.width}x${vp.height}\t${overflowX}\t${status}\n`);
      console.log(`${route} @ ${vp.width}x${vp.height} -> ${status} (overflowX=${overflowX})`);
    }

    await context.close();
  }

  await browser.close();
})();
