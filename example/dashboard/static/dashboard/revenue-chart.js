// Revenue per week: a column chart drawn from the json_script data. Colours come from Tabler's CSS variables, and
// the chart is drawn again when data-bs-theme on <html> changes, so light and dark mode both read well.
(function () {
  const element = document.getElementById("chart-revenue");
  const source = document.getElementById("revenue-data");
  if (!element || !source || !window.ApexCharts) return;
  const data = JSON.parse(source.textContent);
  let chart = null;

  function css(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function draw() {
    if (chart) chart.destroy();
    const dark = document.documentElement.getAttribute("data-bs-theme") === "dark";
    chart = new ApexCharts(element, {
      chart: { type: "bar", height: 260, fontFamily: "inherit", toolbar: { show: false }, parentHeightOffset: 0, background: "transparent" },
      theme: { mode: dark ? "dark" : "light" },
      colors: [css("--tblr-primary")],
      series: [{ name: "Revenue", data: data.values }],
      xaxis: {
        categories: data.labels,
        axisBorder: { show: false },
        axisTicks: { show: false },
        tooltip: { enabled: false },
        labels: { style: { colors: css("--tblr-secondary-color") } },
      },
      yaxis: {
        min: 0,
        forceNiceScale: true,
        labels: { formatter: (v) => "€ " + Math.round(v).toLocaleString("en"), style: { colors: css("--tblr-secondary-color") } },
      },
      grid: { borderColor: css("--tblr-border-color"), strokeDashArray: 4 },
      plotOptions: { bar: { borderRadius: 3, columnWidth: "60%" } },
      dataLabels: { enabled: false },
      tooltip: { y: { formatter: (v) => "€ " + v.toLocaleString("en", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) } },
    });
    chart.render();
  }

  draw();
  new MutationObserver(draw).observe(document.documentElement, { attributes: true, attributeFilter: ["data-bs-theme"] });
})();
