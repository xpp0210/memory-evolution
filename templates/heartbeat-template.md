# HEARTBEAT.md - 周期性维护任务

## 🔄 记忆维护（每次心跳）

### 1. 自进化反思检查（每次心跳必做）
- [ ] 运行 `bash ~/.openclaw/workspace/scripts/reflect.sh` 查看技能状态
- [ ] 如有 fail_count >= 3 的技能，分析失败模式并优化
- [ ] 将本次会话的任务结果路由到对应 skill 并更新计数器

### 2. 记忆整理
- [ ] 查看最近 3 天的 `memory/YYYY-MM-DD.md`
- [ ] 将重要内容提炼到 `MEMORY.md`
- [ ] 清理过时信息

### 3. 收集箱清理
- [ ] 检查 Obsidian `01-收集箱/` 是否有待整理笔记
- [ ] 如有，移动到合适目录

### 4. 项目状态
- [ ] 检查 `03-项目/` 下的进行中项目
- [ ] 更新进度（如有变化）

### 5. MEMORY.md 健康检查（每周一次）
- [ ] 运行 `~/.openclaw/workspace/scripts/check-memory-health.sh`
- [ ] 总行数 > 500 → 立即优化
- [ ] 单章节 > 100 行 → 精简到核心要点

### 6. 归档管理（每周一次）
- [ ] 检查 `memory/archive/` 目录
- [ ] 删除超过30天的归档文件

### 7. VikingDB 知识同步（每次心跳）
- [ ] 运行 `~/.openclaw/workspace/scripts/sync-obsidian-to-viking.sh` 增量同步

---

## ⏰ 检查频率控制

使用 `memory/heartbeat-state.json` 跟踪上次检查时间。

**规则**：
- 同类检查间隔 ≥ 4 小时
- 深夜（23:00-08:00）不主动打扰
- 无新内容时保持安静（HEARTBEAT_OK）
- MEMORY.md 健康检查：每周一次
- 归档清理：每周一次

---

## 📋 当前状态

启用时间：2026-03-07 23:21
自进化激活：2026-03-31
