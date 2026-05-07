const { addTitleBlock, addPageBadge, addCard, addArrowGlyph, addLine } = require("./helpers");

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg };

  addTitleBlock(slide, "Phase D-2 Feature Extraction Pipeline", "How one spectrum is converted into 38 routing features");
  addPageBadge(slide, pres, 1, theme);

  addCard(slide, pres, {
    x: 0.40, y: 1.05, w: 1.25, h: 3.55, fill: "F5F7FA",
    title: "Input",
    body: "R_total(λ)\n\nΔR_total(λ)\n\nreference spectrum\n+\ncase spectrum",
    titleSize: 19, bodySize: 14.5, bodyY: 0.54
  });

  const branchX = 1.95;
  const branchW = 2.40;
  const branchH = 0.66;
  const branchBody = 12.4;
  const branches = [
    {
      y: 1.00, fill: "DDEAFB", title: "Windowed energy features",
      body: "Input: ΔR_total\nCore: front / transition / rear windows\nOutput: front_rms, rear_rms,\nfront/rear ratio"
    },
    {
      y: 1.80, fill: "E5F3E4", title: "Rear-window shift features",
      body: "Input: rear-window R_total\nCore: reference vs case,\nbest alignment\nOutput: best shift, explained fraction,\nresidual"
    },
    {
      y: 2.70, fill: "F7EBDD", title: "Rear-window spectral features",
      body: "Input: rear-window signal\nCore: uniform 1/λ grid +\nfrequency analysis\nOutput: dominant freq, bandwidth,\nsideband, complexity"
    },
    {
      y: 3.60, fill: "EEE6F9", title: "Wavelet features",
      body: "Input: ΔR_total\nCore: localized scale-space\ndecomposition\nOutput: front / transition / rear\nenergy + entropy"
    },
    {
      y: 4.40, fill: "FBE7EC", title: "Template similarity features",
      body: "Input: ΔR_total\nCore: compare against family mean\ntemplates\nOutput: thickness / front roughness /\nrear roughness / front gap /\nrear gap similarity"
    }
  ];
  branches.forEach((item, i) => {
    addCard(slide, pres, {
      x: branchX, y: item.y, w: branchW, h: branchH + (i >= 2 ? 0.18 : 0.10) + (i === 4 ? 0.24 : 0),
      fill: item.fill, title: item.title, body: item.body, titleSize: 14.8, bodySize: branchBody, bodyY: 0.44
    });
    addLine(slide, pres, 1.68, 2.86, 0.20, item.y + 0.30 - 2.86);
  });

  addArrowGlyph(slide, 1.70, 2.73, 0.18, 0.22);
  addCard(slide, pres, {
    x: 4.68, y: 1.32, w: 1.52, h: 3.02, fill: "EAE7F7",
    title: "38 quantitative features",
    body: "window amplitudes\nratios\nshift metrics\nrear spectral metrics\nwavelet metrics\ntemplate-similarity metrics",
    titleSize: 15.8, bodySize: 13.3, bodyY: 0.60
  });

  branches.forEach((item, i) => {
    const yCenter = item.y + (i >= 2 ? 0.43 : 0.34);
    addLine(slide, pres, 4.40, yCenter, 0.18, 2.82 - yCenter);
  });
  addArrowGlyph(slide, 4.46, 2.72, 0.18, 0.22);

  const useX = 6.55;
  const uses = [
    { y: 1.02, title: "PCA / UMAP visualization", body: "low-dimensional map for quick\nfamily separation" },
    { y: 2.14, title: "automatic routing", body: "choose the likely defect family\nbefore fitting" },
    { y: 3.26, title: "family-specific full-spectrum fitting", body: "send the routed case into the\nmatching full-spectrum fitter" }
  ];
  uses.forEach((item) => {
    addCard(slide, pres, {
      x: useX, y: item.y, w: 2.75, h: 0.84, fill: "EEF1F4",
      title: item.title, body: item.body, titleSize: 14.6, bodySize: 12.7, bodyY: 0.44
    });
  });
  addLine(slide, pres, 6.28, 2.82, 0.20, -1.34);
  addLine(slide, pres, 6.28, 2.82, 0.20, -0.22);
  addLine(slide, pres, 6.28, 2.82, 0.20, 0.90);
  addArrowGlyph(slide, 6.34, 1.38, 0.14, 0.18);
  addArrowGlyph(slide, 6.34, 2.50, 0.14, 0.18);
  addArrowGlyph(slide, 6.34, 3.62, 0.14, 0.18);
}

module.exports = { createSlide };
