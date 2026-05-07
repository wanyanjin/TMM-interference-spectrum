const pptxgen = require("pptxgenjs");
const { createSlide: slide01 } = require("./slide-01");
const { createSlide: slide02 } = require("./slide-02");
const { createSlide: slide03 } = require("./slide-03");
const fs = require("fs");
const path = require("path");

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "OpenAI Codex";
  pres.company = "TMM-interference-spectrum";
  pres.subject = "Phase D-2 feature extraction explainer";
  pres.title = "feature_extraction_explainer";
  pres.lang = "en-US";
  pres.theme = {
    headFontFace: "Arial",
    bodyFontFace: "Arial",
    lang: "en-US"
  };

  const theme = {
    primary: "223041",
    secondary: "5E6B78",
    accent: "8391A0",
    light: "E9EEF3",
    bg: "FCFDFE"
  };

  slide01(pres, theme);
  slide02(pres, theme);
  slide03(pres, theme);

  const outDir = path.resolve(__dirname, "../slides/output");
  const rootCopy = path.resolve(__dirname, "../feature_extraction_explainer.pptx");
  fs.mkdirSync(outDir, { recursive: true });
  const outputPath = path.join(outDir, "feature_extraction_explainer.pptx");
  await pres.writeFile({ fileName: outputPath });
  fs.copyFileSync(outputPath, rootCopy);
  console.log(`Wrote ${outputPath}`);
  console.log(`Copied ${rootCopy}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
