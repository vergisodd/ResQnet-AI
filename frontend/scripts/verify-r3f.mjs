import { mkdir } from 'node:fs/promises';
import { chromium } from 'playwright';
import { PNG } from 'pngjs';

const targets = [
  { name: 'desktop', viewport: { width: 1440, height: 1000 } },
  { name: 'mobile', viewport: { width: 390, height: 844 } }
];

await mkdir('test-artifacts', { recursive: true });

const browser = await chromium.launch();
const failures = [];

for (const target of targets) {
  const page = await browser.newPage({ viewport: target.viewport });
  const consoleErrors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });

  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle' });
  await page.waitForFunction(() => document.querySelectorAll('canvas').length >= 1, null, { timeout: 20000 });
  await page.locator('#global').scrollIntoViewIfNeeded();
  await page.waitForFunction(() => document.querySelectorAll('canvas').length >= 2, null, { timeout: 20000 });
  await page.waitForTimeout(1600);
  const screenshot = await page.screenshot({
    path: `test-artifacts/r3f-${target.name}.png`,
    fullPage: true
  });

  const rects = await page.locator('canvas').evaluateAll((items) =>
    items.map((item) => {
      const rect = item.getBoundingClientRect();
      return {
        x: rect.x + window.scrollX,
        y: rect.y + window.scrollY,
        width: rect.width,
        height: rect.height
      };
    })
  );
  const png = PNG.sync.read(screenshot);
  const results = rects.map((rect, index) => {
    if (!rect) return { ok: false, reason: 'missing-canvas-rect' };
    let litSamples = 0;
    const samplePoints = [0.22, 0.34, 0.46, 0.58, 0.7, 0.82];

    for (const xRatio of samplePoints) {
      for (const yRatio of samplePoints) {
        const x = Math.min(png.width - 1, Math.max(0, Math.floor(rect.x + rect.width * xRatio)));
        const y = Math.min(png.height - 1, Math.max(0, Math.floor(rect.y + rect.height * yRatio)));
        const offset = (png.width * y + x) * 4;
        const r = png.data[offset];
        const g = png.data[offset + 1];
        const b = png.data[offset + 2];
        const a = png.data[offset + 3];
        if (a > 0 && r + g + b > 32) litSamples += 1;
      }
    }

    return {
      ok: litSamples >= 6,
      index,
      width: Math.round(rect.width),
      height: Math.round(rect.height),
      litSamples
    };
  });
  const transitionProgress = await page.evaluate(() => {
    const root = document.querySelector('.cinematic-root');
    if (!root) return 0;
    return Number(getComputedStyle(root).getPropertyValue('--scene-progress')) || 0;
  });

  if (results.some((result) => !result.ok) || transitionProgress < 0.65 || consoleErrors.length) {
    failures.push({ target: target.name, results, transitionProgress, consoleErrors });
  } else {
    console.log(
      `${target.name}: ${results
        .map((result) => `canvas ${result.index} ${result.width}x${result.height}, lit samples ${result.litSamples}`)
        .join(' | ')} | transition progress ${transitionProgress.toFixed(2)}`
    );
  }

  await page.close();
}

await browser.close();

if (failures.length) {
  console.error(JSON.stringify(failures, null, 2));
  process.exit(1);
}
