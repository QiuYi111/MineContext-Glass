# Glass WebUI 规划（Standalone 版本）

## 1. 总体目标

将 Glass WebUI 打造成一个完全独立、开箱即用的体验。前端依然保持炫酷的玻璃拟态 + 霓虹动效，但后端只保留与 `glass start` CLI 等价的轻量链路（视频 ingestion → manifest 对齐 → 报告生成），不再依赖 OpenContext 主程序。

## 2. 核心原则

1. **轻量后端**：复用 `glass start` 现有逻辑，打包成单独服务（FastAPI/Flask 或 Node），接口与当前 `/glass/*` 完全一致。
2. **独立前端**：`glass/webui` 使用 Vite + React，默认指向轻量后端；支持通过环境变量切换至真实服务器。
3. **显式生成按钮**：前端提供 “Generate Daily Report” CTA，用户手动触发报告生成，搭配动效与状态反馈。
4. **可演示**：提供 Demo/Mock 数据，`npm run dev:demo` 即可演示；需要跑真实流水线时，`npm run dev:real` 指向轻量后端。
5. **高质量体验**：保持动效、Toast、视觉卡片等增强功能，同时保证错误提示与流程状态清晰。

## 3. 实施路线（6~7 天）

| 阶段                          | 说明                                                                                                                                                           | 预估   |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| 轻量后端 服务                | 提供 `/uploads/limits`、`/upload`、`/status/:id`、`/report/:id`（GET/PUT）、`/report/:id/generate`；内部直接调用 `glass` 包的 ingestion/processing | 2 天   |
| Demo 数据层                   | 提供示例 timeline、高光、视觉卡片 JSON，前端可一键进入 demo 模式                                                                                               | 1 天   |
| “Generate Daily Report” CTA | UI 按钮、动效与状态控制，调用生成接口                                                                                                                          | 1.5 天 |
| 文档 & 脚本                   | README、启动脚本（dev/demo/real），配置参数说明                                                                                                                | 0.5 天 |
| 自动化测试                    | 前端 Playwright（mock + real），后端 pytest（轻量服务）                                                                                                        | 1 天   |
| 视觉微调 & 验收               | 细节打磨、截图/录屏                                                                                                                                            | 1 天   |

## 4. 交付内容

- `glass/webui` 前端：新增 `GenerateAction` 组件、API 层真实、数据入口。
- 轻量后端：紧凑版 FastAPI/Flask 应用，可单独运行，或提供 Docker 镜像。
- 文档：更新 README、`webui_plan.md`、PRD；明确如何运行 demo/真实模式。
- 测试：Playwright/Cypress + pytest 确保功能与 CLI 一致。

## 5. 风险与对策

| 风险               | 缓解策略                                                     |
| ------------------ | ------------------------------------------------------------ |
| 真实数据不一致     | 统一接口合同，前端用 TypeScript 类型约束，后端写集成测试     |
| 包体积膨胀         | 持续关注 `vite build` 结果，必要时做按需加载               |
| 生成按钮滥用       | 前端节流、后端加速率限制或状态锁定                           |
| CLI 与服务逻辑偏差 | 尽量直接复用 `glass` 包中的 ingestion/processing，减少复制 |

## 6. 下一步行动

1. 起草轻量后端骨架（复用 `GlassIngestionService` 及报告生成逻辑）。
2. 前端新增 `GenerateAction` 按钮与 API 切换逻辑。
3. 准备 demo 数据和模式切换文档。
4. 完成测试与视觉微调，输出最终演示版本。
