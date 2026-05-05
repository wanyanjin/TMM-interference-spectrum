const CARD_LINE = "9CA9B8";
const FLOW_LINE = "7F8FA3";

function addTitleBlock(slide, title, subtitle) {
  slide.addText(title, {
    x: 0.45, y: 0.24, w: 9.0, h: 0.34,
    fontFace: "Arial", fontSize: 24, bold: true, color: "223041", margin: 0, fit: "shrink"
  });
  slide.addText(subtitle, {
    x: 0.45, y: 0.58, w: 8.9, h: 0.22,
    fontFace: "Arial", fontSize: 15.5, color: "5E6B78", margin: 0, fit: "shrink"
  });
}

function addPageBadge(slide, pres, num, theme) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 9.12, y: 5.08, w: 0.44, h: 0.28,
    rectRadius: 0.08,
    fill: { color: theme.accent },
    line: { color: theme.accent, width: 0.8 }
  });
  slide.addText(String(num), {
    x: 9.12, y: 5.08, w: 0.44, h: 0.28,
    fontFace: "Arial", fontSize: 11, bold: true, color: "FFFFFF",
    align: "center", valign: "middle", margin: 0
  });
}

function addCard(slide, pres, cfg) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: cfg.x, y: cfg.y, w: cfg.w, h: cfg.h,
    rectRadius: cfg.r || 0.08,
    fill: { color: cfg.fill },
    line: { color: cfg.line || CARD_LINE, width: 1.0 }
  });
  slide.addText(cfg.title, {
    x: cfg.x + 0.12, y: cfg.y + 0.09, w: cfg.w - 0.24, h: cfg.titleH || 0.34,
    fontFace: "Arial", fontSize: cfg.titleSize || 16, bold: true, color: "223041", margin: 0, fit: "shrink"
  });
  slide.addText(cfg.body, {
    x: cfg.x + 0.12, y: cfg.y + (cfg.bodyY || 0.48), w: cfg.w - 0.24, h: cfg.bodyH || (cfg.h - 0.60),
    fontFace: "Arial", fontSize: cfg.bodySize || 13.5, bold: false, color: "334252",
    margin: 0, breakLine: false, fit: "shrink", valign: "top"
  });
}

function addArrowGlyph(slide, x, y, w, h) {
  slide.addText("→", {
    x, y, w, h, fontFace: "Arial", fontSize: 20, bold: true,
    color: FLOW_LINE, align: "center", valign: "middle", margin: 0
  });
}

function addLine(slide, pres, x, y, w, h) {
  slide.addShape(pres.shapes.LINE, {
    x, y, w, h, line: { color: FLOW_LINE, width: 1.1 }
  });
}

function addTag(slide, pres, x, y, w, h, text, color) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.06,
    fill: { color: color.fill },
    line: { color: color.line, width: 0.9 }
  });
  slide.addText(text, {
    x, y: y + 0.01, w, h: h - 0.01,
    fontFace: "Arial", fontSize: 12.5, bold: true, color: color.text,
    align: "center", valign: "middle", margin: 0, fit: "shrink"
  });
}

function addSectionBand(slide, pres, x, y, w, h, fill, label) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: fill, transparency: 38 },
    line: { color: fill, transparency: 100, width: 0.1 }
  });
  slide.addText(label, {
    x, y: y + 0.01, w, h: 0.18,
    fontFace: "Arial", fontSize: 12.5, bold: true, color: "5A6775",
    align: "center", margin: 0
  });
}

module.exports = {
  addTitleBlock,
  addPageBadge,
  addCard,
  addArrowGlyph,
  addLine,
  addTag,
  addSectionBand
};
