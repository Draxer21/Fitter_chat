const { test } = require('playwright/test');
const fs = require('fs');
const path = require('path');

const base = 'http://127.0.0.1:4173';
const viewports = [
  { name: '320', width: 320, height: 720 },
  { name: '375', width: 375, height: 812 },
  { name: '768', width: 768, height: 1024 },
  { name: '1024', width: 1024, height: 768 },
  { name: '1440', width: 1440, height: 900 },
];
const routes = ['/', '/login', '/chat', '/catalogo', '/pago'];

const outDir = '/tmp/fitter-responsive';
fs.mkdirSync(outDir, { recursive: true });

for (const vp of viewports) {
  for (const route of routes) {
    test(`${route} @ ${vp.name}`, async ({ browser }) => {
      const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
      const page = await context.newPage();
      await page.goto(`${base}${route}`, { waitUntil: 'networkidle', timeout: 45000 });
      await page.waitForTimeout(700);

      const metrics = await page.evaluate(() => {
        const doc = document.documentElement;
        const body = document.body;
        const scrollW = Math.max(doc.scrollWidth, body ? body.scrollWidth : 0);
        const innerW = window.innerWidth;
        const overflowX = Math.max(0, scrollW - innerW);
        return { scrollW, innerW, overflowX, href: location.href, title: document.title };
      });

      const routeName = route === '/' ? 'home' : route.replace(/\//g, '_').replace(/^_/, '');
      const shot = path.join(outDir, `${routeName}-${vp.name}.png`);
      await page.screenshot({ path: shot, fullPage: true });

      const line = `${route}\t${vp.width}x${vp.height}\toverflowX=${metrics.overflowX}`;
      fs.appendFileSync(path.join(outDir, 'summary.tsv'), `${line}\n`);

      if (metrics.overflowX > 1) {
        fs.appendFileSync(path.join(outDir, 'issues.tsv'), `${line}\n`);
      }

      await context.close();
    });
  }
}
