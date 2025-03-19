// 必需：配置 Tailwind 的暗黑模式
tailwind.config = {
  darkMode: "class",
  corePlugins: {
    // 确保需要的插件都被包含
    preflight: true,
  },
};

// 在页面加载时初始化主题
document.addEventListener("DOMContentLoaded", function () {
  const savedTheme = localStorage.getItem("theme") || "light";
  document.documentElement.classList.toggle("dark", savedTheme === "dark");
});
function toggleTheme() {
  const html = document.documentElement;
  html.classList.toggle("dark");
  const newTheme = html.classList.contains("dark") ? "dark" : "light";
  localStorage.setItem("theme", newTheme);
}
