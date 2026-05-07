const { addTitleBlock, addPageBadge, addCard, addLine, addArrowGlyph } = require("./helpers");

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg };

  addTitleBlock(slide, "Phase D-2 Feature Groups Overview", "Five complementary feature sources for defect routing");
  addPageBadge(slide, pres, 2, theme);

  const cards = [
    {
      x: 0.45, y: 1.02, w: 2.30, h: 1.54, fill: "DDEAFB", title: "Windowed energy features",
      body: "Input\nΔR_total(λ)\n\nOutput\nfront_rms, rear_rms,\nfront/rear ratio\n\nQuestion answered\nWhere does the change mainly live?"
    },
    {
      x: 2.95, y: 1.02, w: 2.30, h: 1.54, fill: "E5F3E4", title: "Rear-window shift features",
      body: "Input\nrear-window R_total(λ)\n\nOutput\nbest shift, explained fraction,\nresidual\n\nQuestion answered\nDoes it behave like thickness shift?"
    },
    {
      x: 5.45, y: 1.02, w: 2.30, h: 1.54, fill: "F7EBDD", title: "Rear-window spectral features",
      body: "Input\nrear aligned residual\n\nOutput\ndominant freq, bandwidth,\nsideband, complexity\n\nQuestion answered\nIs there extra rear-window complexity?"
    },
    {
      x: 0.45, y: 2.92, w: 2.30, h: 1.72, fill: "EEE6F9", title: "Wavelet features",
      body: "Input\nΔR_total(λ)\n\nOutput\nfront/transition/rear energy,\nentropy, peak scale\n\nQuestion answered\nWhere is the change concentrated,\nand is it locally reconstructed?"
    },
    {
      x: 2.95, y: 2.92, w: 2.30, h: 1.72, fill: "FBE7EC", title: "Template similarity features",
      body: "Input\nΔR_total(λ) vs family templates\n\nOutput\nthickness / front roughness /\nrear roughness / front gap /\nrear gap similarity\n\nQuestion answered\nWhich defect family does it look like overall?"
    },
    {
      x: 5.45, y: 2.92, w: 2.30, h: 1.72, fill: "EEF1F4", title: "Summary route",
      body: "5 groups\n\n38 quantitative features\n\nrouting / embedding /\nfamily-specific fitting"
    }
  ];
  cards.forEach((cfg, idx) => addCard(slide, pres, {
    ...cfg,
    titleSize: idx === 5 ? 16 : 15,
    bodySize: idx >= 3 ? 12.9 : 13.1,
    bodyY: 0.42
  }));

  addLine(slide, pres, 2.78, 1.80, 2.58, 1.72);
  addLine(slide, pres, 5.28, 1.80, 0.14, 1.72);
  addLine(slide, pres, 2.78, 3.78, 2.58, -0.02);
  addLine(slide, pres, 5.28, 3.78, 0.14, -0.02);
  addArrowGlyph(slide, 5.30, 3.38, 0.14, 0.18);
  addArrowGlyph(slide, 5.30, 2.80, 0.14, 0.18);
  addArrowGlyph(slide, 5.30, 2.22, 0.14, 0.18);
}

module.exports = { createSlide };
