const fs = require("fs");
const path = require("path");
const { addTitleBlock, addPageBadge, addCard, addArrowGlyph, addTag, addSectionBand } = require("./helpers");

function readCurves() {
  const csvPath = path.resolve(__dirname, "../../../../../data/processed/phaseD1/phaseD1_rtotal_database.csv");
  const lines = fs.readFileSync(csvPath, "utf8").trim().split(/\r?\n/);
  const header = lines.shift().split(",");
  const idx = Object.fromEntries(header.map((name, i) => [name, i]));
  const caseRows = [];
  const refRows = [];
  for (const line of lines) {
    const cols = line.split(",");
    const family = cols[idx.family];
    const caseId = cols[idx.case_id];
    const anchorId = cols[idx.anchor_id];
    if (family === "rear_gap_on_background" && caseId === "D1_0001" && anchorId === "anchor_01_nominal") {
      caseRows.push({
        wl: Number(cols[idx.Wavelength_nm]),
        r: Number(cols[idx.R_total]),
        d: Number(cols[idx.Delta_R_total_vs_reference])
      });
    }
    if (family === "background_anchor" && caseId === "D1_0001" && anchorId === "anchor_01_nominal") {
      refRows.push({
        wl: Number(cols[idx.Wavelength_nm]),
        r: Number(cols[idx.R_total])
      });
    }
  }
  return {
    caseRows: caseRows.sort((a, b) => a.wl - b.wl),
    refRows: refRows.sort((a, b) => a.wl - b.wl)
  };
}

function buildSeries(rows, key, scale = 1) {
  return rows.map((row) => ({ x: row.wl, y: row[key] * scale }));
}

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg };

  addTitleBlock(slide, "Why not use raw spectra directly?", "Route first, then fit the full spectrum with the matching family-specific model");
  addPageBadge(slide, pres, 3, theme);

  slide.addText("Directly use raw spectra", {
    x: 0.55, y: 0.90, w: 3.90, h: 0.24,
    fontFace: "Arial", fontSize: 16.5, bold: true, color: "223041", margin: 0
  });
  slide.addText("Use feature extraction first", {
    x: 5.35, y: 0.90, w: 3.95, h: 0.24,
    fontFace: "Arial", fontSize: 16.5, bold: true, color: "223041", margin: 0
  });

  const { caseRows, refRows } = readCurves();
  addSectionBand(slide, pres, 0.60, 1.26, 0.82, 2.26, "DDEAFB", "front");
  addSectionBand(slide, pres, 1.42, 1.26, 0.94, 2.26, "F7EBDD", "transition");
  addSectionBand(slide, pres, 2.36, 1.26, 1.05, 2.26, "E5F3E4", "rear");
  slide.addChart(pres.charts.LINE, [
    { name: "reference", labels: buildSeries(refRows, "wl").map((d) => d.x), values: buildSeries(refRows, "r", 100).map((d) => d.y) },
    { name: "case", labels: buildSeries(caseRows, "wl").map((d) => d.x), values: buildSeries(caseRows, "r", 100).map((d) => d.y) }
  ], {
    x: 0.55, y: 1.12, w: 4.15, h: 1.30,
    catAxisLabelFontSize: 9, valAxisLabelFontSize: 9,
    catAxisTitle: "Wavelength (nm)", valAxisTitle: "R_total (%)",
    showLegend: true, legendPos: "r", showTitle: false,
    chartColors: ["7F8C8D", "1565C0"], showValue: false,
    valAxisMinVal: 0, valAxisMaxVal: 80, valAxisMajorUnit: 20,
    lineSize: 2, showCatName: false, showSerName: false
  });
  slide.addChart(pres.charts.LINE, [
    { name: "delta", labels: buildSeries(caseRows, "wl").map((d) => d.x), values: buildSeries(caseRows, "d", 100).map((d) => d.y) }
  ], {
    x: 0.55, y: 2.48, w: 4.15, h: 1.24,
    catAxisLabelFontSize: 9, valAxisLabelFontSize: 9,
    catAxisTitle: "Wavelength (nm)", valAxisTitle: "ΔR_total (%)",
    showLegend: false, showTitle: false,
    chartColors: ["C62828"], showValue: false,
    valAxisMinVal: -0.06, valAxisMaxVal: 0.06, valAxisMajorUnit: 0.03,
    lineSize: 2, showCatName: false, showSerName: false
  });
  addTag(slide, pres, 0.70, 1.84, 1.08, 0.22, "high-dimensional", { fill: "FFF3F3", line: "D8A8A8", text: "6E4950" });
  addTag(slide, pres, 1.90, 1.34, 0.96, 0.22, "hard to explain", { fill: "FFF3F3", line: "D8A8A8", text: "6E4950" });
  addTag(slide, pres, 0.74, 2.82, 0.98, 0.22, "noise-sensitive", { fill: "FFF3F3", line: "D8A8A8", text: "6E4950" });
  addTag(slide, pres, 1.86, 3.30, 1.22, 0.22, "hard to route physically", { fill: "FFF3F3", line: "D8A8A8", text: "6E4950" });

  addCard(slide, pres, {
    x: 5.42, y: 1.36, w: 1.34, h: 0.92, fill: "DDEAFB",
    title: "5 feature groups", body: "window energy\nrear shift\nrear spectrum\nwavelet\ntemplate similarity", titleSize: 15.5, bodySize: 12.3, bodyY: 0.40
  });
  addCard(slide, pres, {
    x: 6.98, y: 1.36, w: 1.08, h: 0.92, fill: "EEE6F9",
    title: "38 features", body: "compact numbers\nwith physical meaning", titleSize: 15.2, bodySize: 12.3, bodyY: 0.40
  });
  addCard(slide, pres, {
    x: 8.26, y: 1.36, w: 1.08, h: 0.92, fill: "E5F3E4",
    title: "routing", body: "choose the likely family\nbefore full-spectrum fit", titleSize: 15.2, bodySize: 12.3, bodyY: 0.40
  });
  addArrowGlyph(slide, 6.79, 1.76, 0.16, 0.16);
  addArrowGlyph(slide, 8.08, 1.76, 0.16, 0.16);

  addTag(slide, pres, 5.62, 2.64, 1.36, 0.26, "lower-dimensional", { fill: "EEF8EF", line: "9BC59E", text: "32494A" });
  addTag(slide, pres, 7.12, 2.64, 1.64, 0.26, "physically interpretable", { fill: "EEF8EF", line: "9BC59E", text: "32494A" });
  addTag(slide, pres, 5.62, 3.18, 1.94, 0.26, "good for classify-then-fit", { fill: "EEF8EF", line: "9BC59E", text: "32494A" });
  addTag(slide, pres, 7.68, 3.18, 1.72, 0.26, "better for automatic routing", { fill: "EEF8EF", line: "9BC59E", text: "32494A" });

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.42, y: 4.20, w: 3.98, h: 0.40, rectRadius: 0.08,
    fill: { color: "FFF5F7" }, line: { color: "D8A4B2", width: 0.9 }
  });
  slide.addText("feature extraction is used for routing, not for replacing full-spectrum fitting", {
    x: 5.56, y: 4.29, w: 3.70, h: 0.16,
    fontFace: "Arial", fontSize: 12.6, bold: true, color: "9C2F56",
    align: "center", margin: 0, fit: "shrink"
  });
}

module.exports = { createSlide };
