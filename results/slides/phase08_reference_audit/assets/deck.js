(function () {
  function splitTopLevel(text) {
    const parts = [];
    let depth = 0;
    let current = "";
    for (const ch of text) {
      if (ch === "{" ) {
        depth += 1;
      } else if (ch === "}" && depth > 0) {
        depth -= 1;
      }
      if (ch === " " && depth === 0) {
        if (current) {
          parts.push(current);
          current = "";
        }
      } else {
        current += ch;
      }
    }
    if (current) {
      parts.push(current);
    }
    return parts;
  }

  function readBraceGroup(source, start) {
    if (source[start] !== "{") {
      return null;
    }
    let depth = 0;
    for (let i = start; i < source.length; i += 1) {
      const ch = source[i];
      if (ch === "{") {
        depth += 1;
      } else if (ch === "}") {
        depth -= 1;
        if (depth === 0) {
          return {
            body: source.slice(start + 1, i),
            end: i + 1,
          };
        }
      }
    }
    return null;
  }

  function convertLatexToHtml(source) {
    let output = "";
    let i = 0;
    while (i < source.length) {
      if (source.startsWith("\\frac", i)) {
        const numerator = readBraceGroup(source, i + 5);
        const denominator = numerator ? readBraceGroup(source, numerator.end) : null;
        if (numerator && denominator) {
          output += `<span class="math-frac"><span class="math-num">${convertLatexToHtml(numerator.body)}</span><span class="math-den">${convertLatexToHtml(denominator.body)}</span></span>`;
          i = denominator.end;
          continue;
        }
      }
      if (source.startsWith("\\mathrm", i) || source.startsWith("\\text", i)) {
        const groupStart = source.indexOf("{", i);
        const group = groupStart >= 0 ? readBraceGroup(source, groupStart) : null;
        if (group) {
          output += convertLatexToHtml(group.body);
          i = group.end;
          continue;
        }
      }
      if (source[i] === "^" || source[i] === "_") {
        const tag = source[i] === "^" ? "sup" : "sub";
        const next = source[i + 1];
        if (next === "{") {
          const group = readBraceGroup(source, i + 1);
          if (group) {
            output += `<${tag}>${convertLatexToHtml(group.body)}</${tag}>`;
            i = group.end;
            continue;
          }
        }
        output += `<${tag}>${next || ""}</${tag}>`;
        i += 2;
        continue;
      }
      if (source[i] === "{") {
        const group = readBraceGroup(source, i);
        if (group) {
          output += convertLatexToHtml(group.body);
          i = group.end;
          continue;
        }
      }
      if (source.startsWith("\\cdot", i)) {
        output += "·";
        i += 5;
        continue;
      }
      if (source.startsWith("\\times", i)) {
        output += "×";
        i += 6;
        continue;
      }
      if (source.startsWith("\\lambda", i)) {
        output += "λ";
        i += 7;
        continue;
      }
      if (source.startsWith("\\,", i) || source.startsWith("\\ ", i)) {
        output += " ";
        i += 2;
        continue;
      }
      if (source[i] === "\\") {
        i += 1;
        continue;
      }
      output += source[i];
      i += 1;
    }
    return output;
  }

  function renderMathFallback() {
    document.querySelectorAll(".formula-card div, .trace-step-body div, .metric-card div, .card p, .card li").forEach((node) => {
      const text = node.textContent?.trim();
      if (!text || !text.includes("$")) {
        return;
      }
      const displayMatch = text.match(/^\$\$(.*)\$\$$/s);
      const inlineMatch = text.match(/^\$(.*)\$$/s);
      const mathSource = displayMatch?.[1] || inlineMatch?.[1];
      if (!mathSource) {
        return;
      }
      const compactSource = splitTopLevel(mathSource).join(" ");
      const html = convertLatexToHtml(compactSource);
      node.innerHTML = `<span class="${displayMatch ? "math-fallback-display" : "math-fallback-inline"}">${html}</span>`;
    });
  }

  function renderMath() {
    if (typeof window.renderMathInElement !== "function") {
      renderMathFallback();
      return;
    }
    renderMathInElement(document.body, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "$", right: "$", display: false },
      ],
      throwOnError: false,
    });
  }

  function initMermaid() {
    if (!window.mermaid) {
      return;
    }
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

  function setFallbackLayout() {
    document.body.classList.remove("deck-enhanced");
    document.body.classList.add("deck-fallback");
    document.querySelectorAll(".slides > section").forEach((node, idx) => {
      node.style.display = "block";
      node.classList.toggle("present", idx === 0);
    });
  }

  function isolatePresentSlide() {
    document.querySelectorAll(".slides > section").forEach((node) => {
      node.style.display = node.classList.contains("present") ? "block" : "none";
    });
  }

  function initFallback() {
    renderMath();
    initMermaid();
    setFallbackLayout();
    window.phase08OverflowWatchdog?.run();
  }

  if (typeof window.Reveal !== "function") {
    initFallback();
    return;
  }

  document.body.classList.add("deck-enhanced");
  const deck = new window.Reveal({
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

  deck.initialize().then(() => {
    renderMath();
    initMermaid();
    isolatePresentSlide();
    window.phase08OverflowWatchdog?.run();
    deck.on("slidechanged", () => {
      isolatePresentSlide();
      window.phase08OverflowWatchdog?.run();
    });
  }).catch(() => {
    initFallback();
  });
})();
