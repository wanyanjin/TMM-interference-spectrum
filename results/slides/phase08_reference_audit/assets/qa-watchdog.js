(function () {
  function checkOverflow(root = document) {
    const items = [];
    root.querySelectorAll("[data-qa-watch]").forEach((node) => {
      node.classList.remove("dev-overflow-outline");
      const xOverflow = node.scrollWidth - node.clientWidth;
      const yOverflow = node.scrollHeight - node.clientHeight;
      if (xOverflow > 1 || yOverflow > 1) {
        node.classList.add("dev-overflow-outline");
        items.push({
          id: node.id || node.dataset.qaWatch || node.tagName.toLowerCase(),
          xOverflow,
          yOverflow,
        });
      }
    });
    return items;
  }

  function showBanner(items) {
    const prior = document.querySelector(".overflow-banner");
    if (prior) prior.remove();
    if (!items.length) return;
    const banner = document.createElement("div");
    banner.className = "overflow-banner";
    banner.textContent = `Overflow warning: ${items.length}`;
    document.body.appendChild(banner);
  }

  window.phase08OverflowWatchdog = {
    run() {
      const items = checkOverflow();
      if (location.search.includes("dev=1")) showBanner(items);
      return items;
    },
  };

  window.addEventListener("load", () => {
    window.phase08OverflowWatchdog.run();
  });
})();
