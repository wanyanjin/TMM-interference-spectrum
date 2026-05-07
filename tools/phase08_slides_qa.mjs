import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const deckPath = path.join(projectRoot, "results", "slides", "phase08_reference_audit", "phase08_reference_audit_deck.html");
const outputDir = path.join(projectRoot, "results", "slides", "phase08_reference_audit", "qa-output");
const screenshotDir = path.join(outputDir, "screenshots");
const reportPath = path.join(outputDir, "qa-report.json");

await fs.mkdir(screenshotDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
const deckUrl = `file://${deckPath}?dev=1`;

await page.goto(deckUrl);
await page.waitForLoadState("load");

const slideCount = await page.locator(".slides > section").count();
const report = [];

for (let index = 0; index < slideCount; index += 1) {
  await page.goto(`${deckUrl}#/${index}`);
  await page.waitForLoadState("load");
  await page.waitForTimeout(150);

  const slideReport = await page.evaluate((idx) => {
    const slides = Array.from(document.querySelectorAll(".slides > section"));
    const slide = slides[idx];
    const watched = slide.querySelectorAll("[data-qa-watch]");
    const offenders = [];

    watched.forEach((node) => {
      const xOverflow = node.scrollWidth - node.clientWidth;
      const yOverflow = node.scrollHeight - node.clientHeight;
      if (xOverflow > 1 || yOverflow > 1) {
        offenders.push({
          id: node.id || node.dataset.qaWatch || node.tagName.toLowerCase(),
          xOverflow,
          yOverflow,
        });
      }
    });

    return {
      slideIndex: idx + 1,
      title: slide.querySelector(".slide-title")?.textContent?.trim() || `slide-${idx + 1}`,
      sectionScrollWidth: slide.scrollWidth,
      sectionClientWidth: slide.clientWidth,
      sectionScrollHeight: slide.scrollHeight,
      sectionClientHeight: slide.clientHeight,
      sectionOverflowX: slide.scrollWidth - slide.clientWidth,
      sectionOverflowY: slide.scrollHeight - slide.clientHeight,
      offenders,
    };
  }, index);

  const screenshotPath = path.join(screenshotDir, `${String(index + 1).padStart(2, "0")}.png`);
  await page.screenshot({ path: screenshotPath });
  report.push({ ...slideReport, screenshot: screenshotPath });
}

await browser.close();
await fs.writeFile(reportPath, JSON.stringify({
  generatedAt: new Date().toISOString(),
  deckPath,
  slideCount,
  report,
}, null, 2));

console.log(reportPath);
