# Glass WebUI (Standalone)

炫酷版 Glass 日报页面，完全独立于 OpenContext 的 Jinja 模板运行。该工程使用 React + Vite，默认使用玻璃拟态 + 动态背景风格。

## 开发命令

```bash
npm install          # 安装依赖

# 启动开发服务器（默认 http://localhost:5174），并自动代理到后端 /glass 接口
npm run dev

# 产出生产构建，结果落在 dist/ 目录
npm run build

# 离线预览构建产物
npm run preview -- --host
```

## 与后端联调

- 默认假设后端位于 `http://127.0.0.1:8765` 并提供 `/glass/*` API。
- 自定义地址时，设置环境变量：

```bash
VITE_GLASS_API_BASE="http://your-host:8765" npm run dev
```

- 若需要 dev 服务器代理到其它主机，可在启动前设置 `GLASS_API_PROXY`：

```bash
GLASS_API_PROXY="http://10.0.0.2:9000" npm run dev
```

## 部署

构建完成后，会生成完整的 `dist/` 目录（包含 `index.html`, `app.js`, `app.css` 等）。将该目录放到任意静态服务器（Nginx、Caddy、OSS 等）即可，无需依赖 OpenContext 的静态资源目录。

> 生产部署时请确保为 `/glass/*` API 配置反向代理或开启 CORS，以便前端可以访问后端。
