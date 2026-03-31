## 以下内容需要添加到 AGENTS.md

### 自动FIX：工具失败自动记录

**触发**：任何工具调用失败时

**动作**：
1. 在 `memory/YYYY-MM-DD.md` 记录：`⚠️ [工具失败] 工具名 | 错误摘要 | 根因`
2. 同类失败 ≥ 2 次 → 追加到 `memory/iteration-rules.md`
3. 修复后记录：`✅ [已修复] 同上 | 解决方案`

### Skill派生：从通用到具体

**触发**：Skill被使用 ≥ 3 次且每次需额外调整

**动作**：派生具体版本，命名 `<原Skill名>-<场景>`，标注 `派生自: <原Skill名>`

### Memory Skill Bank：元记忆技能库

**Skill Bank 位置**：`memory/memory-skills.json`

**工作流程**：
1. 识别场景 → 从 Skill Bank 匹配技能
2. 按技能的 memory_focus 决定记什么、不记什么
3. 任务完成后更新 success/fail 计数

**技能进化规则**：
- fail_count ≥ 3 → 触发 Designer 优化技能
- 新场景无匹配 → 提议新技能
- 每周心跳回顾成功率

### 反思循环：Read→Execute→Reflect→Write

**每次任务完成后自动执行**：
1. ROUTE — 匹配 skill
2. EXECUTE — 执行
3. REFLECT — 用 reflect_checks 自检
4. ATTRIBUTE — 失败时归因
5. WRITE — 更新计数
6. EVOLVE — fail≥3 时优化

### 自我迭代规范

**触发词**：「自我迭代」「复盘」「反思」
**触发条件**：同类错误≥2次 / 用户不满 / 任务严重偏差

**5步流程**：读日志 → 找模式 → 定根因 → 定措施 → 写入规则库

### 每次任务前自检

- [ ] 已读取规则库
- [ ] 是否属于高错误率场景
- [ ] 需求是否清晰
- [ ] 输出前自查质量
