// 统一的可视化工具函数（页面复用）
(function () {
  function $(id) {
    return document.getElementById(id);
  }

  function show(id) {
    var el = $(id);
    if (el) el.classList.remove("d-none");
  }

  function hide(id) {
    var el = $(id);
    if (el) el.classList.add("d-none");
  }

  function withTimeout(promise, ms) {
    var t;
    var timeout = new Promise(function (_, reject) {
      t = setTimeout(function () {
        reject(new Error("timeout"));
      }, ms);
    });
    return Promise.race([promise, timeout]).finally(function () {
      clearTimeout(t);
    });
  }

  var chartIds = new Set();

  function initChart(id) {
    var el = $(id);
    if (!el) return null;
    var inst = echarts.getInstanceByDom(el);
    if (!inst) inst = echarts.init(el);
    chartIds.add(id);
    return inst;
  }

  function resizeAll() {
    chartIds.forEach(function (id) {
      var el = $(id);
      if (!el) return;
      var inst = echarts.getInstanceByDom(el);
      if (inst) inst.resize();
    });
  }

  window.addEventListener("resize", function () {
    // 轻量防抖，避免 resize 过于频繁
    clearTimeout(window.__dashResizeTimer);
    window.__dashResizeTimer = setTimeout(resizeAll, 120);
  });

  function fetchJson(url, opts) {
    opts = opts || {};
    var timeoutMs = opts.timeoutMs || 10000;
    return withTimeout(
      fetch(url, { credentials: "same-origin" }).then(function (r) {
        if (!r.ok) throw new Error("http_" + r.status);
        return r.json();
      }),
      timeoutMs
    );
  }

  function formatCompactNumber(n) {
    if (n == null || n === "" || isNaN(Number(n))) return "—";
    var v = Number(n);
    var abs = Math.abs(v);
    if (abs >= 1e8) return (v / 1e8).toFixed(2) + "亿";
    if (abs >= 1e4) return (v / 1e4).toFixed(2) + "万";
    return Math.round(v).toLocaleString("zh-CN");
  }

  function formatRmb(n) {
    if (n == null || n === "" || isNaN(Number(n))) return "—";
    return "¥" + formatCompactNumber(n);
  }

  // 统一 ECharts 默认（可按需扩展）
  function baseGrid() {
    return { left: "12%", right: "10%", top: "14%", bottom: "16%" };
  }

  function baseSplitLine() {
    return { show: true, lineStyle: { type: "dashed", opacity: 0.35 } };
  }

  // 对外暴露
  window.Dash = {
    $: $,
    show: show,
    hide: hide,
    initChart: initChart,
    resizeAll: resizeAll,
    fetchJson: fetchJson,
    formatCompactNumber: formatCompactNumber,
    formatRmb: formatRmb,
    baseGrid: baseGrid,
    baseSplitLine: baseSplitLine,
  };
})();

