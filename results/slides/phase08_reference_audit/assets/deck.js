(function () {
  const deck = new Reveal({
    controls: true,
    progress: true,
    center: false,
    hash: true,
    width: 1600,
    height: 900,
    margin: 0.02,
    transition: "slide",
    disableLayout: false,
    keyboard: true,
    overview: true,
  });

  function renderMath() {
    renderMathInElement(document.body, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "$", right: "$", display: false },
      ],
      throwOnError: false,
    });
  }

  function initMermaid() {
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "loose",
      theme: "base",
      themeVariables: {
        primaryColor: "#eef4ff",
        primaryTextColor: "#101828",
        primaryBorderColor: "#d0d5dd",
        lineColor: "#667085",
        secondaryColor: "#fffaeb",
        tertiaryColor: "#ecfdf3",
        fontFamily: '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
      },
      flowchart: { curve: "basis", htmlLabels: true },
    });
    document.querySelectorAll(".mermaid").forEach((node, idx) => {
      const source = node.textContent;
      mermaid.render(`phase08-mermaid-${idx}`, source).then(({ svg }) => {
        node.innerHTML = svg;
      });
    });
  }

  function isolatePresentSlide() {
    document.querySelectorAll(".slides > section").forEach((node) => {
      node.style.display = node.classList.contains("present") ? "block" : "none";
    });
  }

  deck.initialize().then(() => {
    renderMath();
    initMermaid();
    isolatePresentSlide();
    window.phase08OverflowWatchdog?.run();
    deck.on("slidechanged", () => {
      isolatePresentSlide();
      window.phase08OverflowWatchdog?.run();
    });
  });
})();
