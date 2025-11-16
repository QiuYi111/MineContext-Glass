# MineContext Figma Plugin

让Figma设计能够直接与MineContext Glass后端API通信的插件。

## 功能特性

- ✅ 视频上传到后端
- ✅ 获取时间线列表
- ✅ 查看和生成日报
- ✅ 实时状态显示
- ✅ 可配置API地址

## 安装使用

### 1. 在Figma中安装插件

1. 打开Figma
2. 进入 `Plugins > Development > Import plugin from manifest...`
3. 选择本目录下的 `manifest.json` 文件
4. 插件安装完成，可以通过 `Plugins > MineContext API Connector` 启动

### 2. 配置后端地址

在插件中设置后端API地址：
- 开发环境：`http://localhost:8000`
- 生产环境：根据实际部署地址调整

### 3. 使用功能

#### 视频上传
1. 点击"选择视频文件"
2. 选择要上传的视频文件
3. 等待上传完成

#### 时间线管理
1. 点击"加载时间线列表"
2. 查看所有已上传的视频时间线
3. 点击时间线进行选择

#### 日报操作
1. 先选择一个时间线
2. 点击"获取日报"查看已有报告
3. 点击"生成新日报"触发AI生成

## 技术架构

### 插件结构
```
figma-plugin/
├── manifest.json    # Figma插件配置
├── code.js          # 插件主代码（运行在沙箱环境）
├── ui.html          # 用户界面HTML
└── README.md        # 说明文档
```

### API接口

插件调用以下MineContext Glass API：

- `GET /glass/uploads/limits` - 获取上传配额
- `GET /glass/timelines` - 获取时间线列表
- `POST /glass/upload` - 上传视频文件
- `GET /glass/report/{timelineId}` - 获取日报
- `POST /glass/report/{timelineId}/generate` - 生成日报

### 权限说明

- 插件需要网络权限访问外部API
- 文件上传通过浏览器原生API处理
- 所有API调用包含用户凭证

## 开发说明

### 修改API地址
在 `code.js` 中修改 `MINECONTEXT_API_BASE` 常量：
```javascript
const MINECONTEXT_API_BASE = "http://your-api-server:8000";
```

### 添加新功能
1. 在 `code.js` 中添加API调用函数
2. 在 `ui.html` 中添加UI界面
3. 更新消息处理逻辑

### 调试
1. 打开Figma开发者控制台查看日志
2. 插件UI中的操作日志显示详细执行状态
3. 浏览器网络面板监控API请求

## 注意事项

1. **CORS配置**：后端需要允许来自Figma的跨域请求
2. **网络环境**：确保Figma能够访问到后端API地址
3. **文件大小**：注意视频文件大小限制
4. **认证**：API可能需要用户登录状态

## 故障排除

### 上传失败
- 检查后端服务是否启动
- 确认API地址配置正确
- 查看浏览器网络请求详情

### 无法获取数据
- 检查网络连接
- 确认后端API可访问
- 查看插件操作日志

### 插件无法启动
- 确认manifest.json路径正确
- 重启Figma应用
- 检查插件文件完整性