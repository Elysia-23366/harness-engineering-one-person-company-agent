-- =================================================================
-- Harness Engineering · DB Migration v1.0
-- =================================================================
-- 灵感:武艺《Harness Engineering 闭门分享 · 2026-04-28》
-- 三库记忆架构 + Sensors 自进化日志 + Guides 规则表
--
-- 执行方式:
--   sqlite3 backend/data/agent_playground.db < backend/scripts/harness_migration.sql
--
-- 回滚方式:
--   DROP TABLE event_memory;
--   DROP TABLE persona_perception;
--   DROP TABLE relationship_node;
--   DROP TABLE sensor_event;
--   DROP TABLE guide_rule;
-- =================================================================


-- ----- 库 1 · 事件库(Episodic) · 衰减式 -------------------------
-- 武艺原话:"事件库存发生了什么,有情绪标签,会随聊得久而衰减,
--          但峰值点会留下来"
CREATE TABLE IF NOT EXISTS event_memory (
  id TEXT PRIMARY KEY,
  workflow_id TEXT NOT NULL,
  conversation_id TEXT,
  agent_id TEXT NOT NULL,                -- 哪个岗位产生的事件
  user_id TEXT NOT NULL DEFAULT 'ceo',   -- 谁的事件(默认 CEO)
  content TEXT NOT NULL,                 -- 事件内容(摘要,不超过 500 字)
  emotion_tag TEXT NOT NULL DEFAULT 'neutral',  -- neutral|positive|negative|urgent|breakthrough
  importance_score REAL NOT NULL DEFAULT 5.0,   -- 0-9 重要性评分(武艺原版)
  importance_emotion REAL DEFAULT 0,            -- 维度1:情绪激烈度 0-3
  importance_novelty REAL DEFAULT 0,            -- 维度2:是否带来新素材 0-3
  importance_relation REAL DEFAULT 0,           -- 维度3:是否影响关系 0-3
  decay_rate REAL NOT NULL DEFAULT 0.05,        -- 衰减率(每天)
  created_at TEXT NOT NULL,                     -- ISO 8601
  last_accessed_at TEXT,                        -- 最近一次被召回的时间
  access_count INTEGER NOT NULL DEFAULT 0,      -- 被召回次数
  is_active INTEGER NOT NULL DEFAULT 1,         -- 1=活跃 0=已淡出(score<2.0 自动归零)
  metadata_json TEXT                            -- 扩展元数据(JSON)
);

CREATE INDEX IF NOT EXISTS idx_event_memory_agent ON event_memory(agent_id);
CREATE INDEX IF NOT EXISTS idx_event_memory_workflow ON event_memory(workflow_id);
CREATE INDEX IF NOT EXISTS idx_event_memory_score ON event_memory(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_event_memory_active ON event_memory(is_active) WHERE is_active = 1;


-- ----- 库 2 · 角色认知库(Persona Perception) · 永久 ----------------
-- 武艺原话:"角色对用户形成怎样的理解,这是不会衰减的,像你对好朋友的理解"
-- 17 个 agent × 1 个 CEO = 最多 17 行(每个 agent 1 条认知卡)
CREATE TABLE IF NOT EXISTS persona_perception (
  id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL,
  user_id TEXT NOT NULL DEFAULT 'ceo',
  perception_summary TEXT NOT NULL DEFAULT '',   -- 累积印象(LLM 生成的 200 字内)
  trait_keywords TEXT NOT NULL DEFAULT '[]',     -- JSON list: ['谨慎','收敛型聪明',...]
  interaction_count INTEGER NOT NULL DEFAULT 0,  -- 交互次数(用于成熟度判断)
  confidence_level REAL NOT NULL DEFAULT 0.0,    -- 认知信度 0-1
  last_event_id TEXT,                            -- 上次更新源自哪个事件
  created_at TEXT NOT NULL,
  last_updated TEXT NOT NULL,
  UNIQUE(agent_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_persona_perception_agent ON persona_perception(agent_id);


-- ----- 库 3 · 关系节点库(Relationship) · 永久 + 每对独立 ------------
-- 武艺原话:"每个用户的决策观点是独立的,17 岗位对每个用户都是独立的关系坐标"
CREATE TABLE IF NOT EXISTS relationship_node (
  id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL,
  user_id TEXT NOT NULL DEFAULT 'ceo',
  trust_level REAL NOT NULL DEFAULT 0.5,         -- 信任度 0-1
  familiarity REAL NOT NULL DEFAULT 0.0,         -- 熟悉度 0-1
  collaboration_count INTEGER NOT NULL DEFAULT 0,-- 协作次数
  alignment_score REAL NOT NULL DEFAULT 0.5,     -- 价值观对齐度 0-1
  milestones_json TEXT NOT NULL DEFAULT '[]',    -- JSON: [{date, event_id, summary}]
  current_phase TEXT DEFAULT 'cold_start',       -- cold_start|warming|established|deep
  created_at TEXT NOT NULL,
  last_updated TEXT NOT NULL,
  UNIQUE(agent_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_relationship_node_agent ON relationship_node(agent_id);


-- ----- Sensors 自进化日志 -----------------------------------------
-- 武艺原话:"命中率下降意味着系统出问题,会触发自动调整评估规则"
CREATE TABLE IF NOT EXISTS sensor_event (
  id TEXT PRIMARY KEY,
  workflow_id TEXT,
  conversation_id TEXT,
  agent_id TEXT,
  sensor_type TEXT NOT NULL,    -- recall_hit_rate|persona_drift|output_compliance|importance_calibration
  metric_value REAL NOT NULL,
  threshold REAL NOT NULL,
  passed INTEGER NOT NULL,      -- 1 = 通过 / 0 = 警报
  remediation TEXT,             -- 触发了什么自纠正措施(JSON)
  raw_data_json TEXT,           -- 原始度量数据
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sensor_event_type ON sensor_event(sensor_type);
CREATE INDEX IF NOT EXISTS idx_sensor_event_agent ON sensor_event(agent_id);
CREATE INDEX IF NOT EXISTS idx_sensor_event_passed ON sensor_event(passed);


-- ----- Guides 规则表(CEO 可编辑) ----------------------------------
-- 武艺原话:"前馈控制就是设规则护栏,这个 AI 能干什么不能干什么"
CREATE TABLE IF NOT EXISTS guide_rule (
  id TEXT PRIMARY KEY,
  agent_id TEXT,                -- NULL = 全局规则,非 NULL = 特定岗位
  rule_type TEXT NOT NULL,      -- output_schema|forbidden_topic|authority_min|tone_constraint|capability_boundary
  rule_name TEXT NOT NULL,      -- 给 CEO 看的名字
  rule_content TEXT NOT NULL,   -- 规则内容(JSON 或自然语言)
  severity TEXT NOT NULL DEFAULT 'warn',  -- warn|block(block = 不通过则 stop-the-line)
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  last_updated TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_guide_rule_agent ON guide_rule(agent_id);
CREATE INDEX IF NOT EXISTS idx_guide_rule_active ON guide_rule(is_active) WHERE is_active = 1;


-- =================================================================
-- 默认 Guides 规则(开箱即用 · CEO 后续可改)
-- =================================================================
-- 全局规则:输出必须是中文(默认中文为主)
INSERT OR IGNORE INTO guide_rule (id, agent_id, rule_type, rule_name, rule_content, severity, is_active, created_at, last_updated)
VALUES (
  'guide_default_zh',
  NULL,
  'tone_constraint',
  '默认中文输出',
  '所有岗位默认用中文输出,除非 CEO 明确要求英文。',
  'warn',
  1,
  datetime('now'),
  datetime('now')
);

-- R01 PM 规则:必须含 PRD 5 字段
INSERT OR IGNORE INTO guide_rule (id, agent_id, rule_type, rule_name, rule_content, severity, is_active, created_at, last_updated)
VALUES (
  'guide_r01_prd_fields',
  'agent_464094c7',
  'output_schema',
  'R01 PRD 5 字段',
  '{"required_fields":["北极星指标","用户画像","JTBD","功能清单","PRD 路线图"],"min_count":3}',
  'warn',
  1,
  datetime('now'),
  datetime('now')
);

-- R03 工程师规则:必须有部署/监控
INSERT OR IGNORE INTO guide_rule (id, agent_id, rule_type, rule_name, rule_content, severity, is_active, created_at, last_updated)
VALUES (
  'guide_r03_deploy_monitor',
  'agent_f1077f1d',
  'output_schema',
  'R03 必带部署+监控',
  '{"required_keywords":["部署","监控","Sentry","埋点"],"min_count":2}',
  'warn',
  1,
  datetime('now'),
  datetime('now')
);

-- R06 reviewer 规则:必须列具体闸 checklist 条目
INSERT OR IGNORE INTO guide_rule (id, agent_id, rule_type, rule_name, rule_content, severity, is_active, created_at, last_updated)
VALUES (
  'guide_r06_gate_items',
  'agent_8b8f65cf',
  'output_schema',
  'R06 必列闸 checklist 条目',
  '{"required_pattern":"checklist|闸|✓|✗|通过|不通过","min_occurrences":3}',
  'block',
  1,
  datetime('now'),
  datetime('now')
);


-- =================================================================
-- 验证 schema 完整性
-- =================================================================
SELECT 'event_memory' AS table_name, COUNT(*) AS row_count FROM event_memory
UNION ALL
SELECT 'persona_perception', COUNT(*) FROM persona_perception
UNION ALL
SELECT 'relationship_node', COUNT(*) FROM relationship_node
UNION ALL
SELECT 'sensor_event', COUNT(*) FROM sensor_event
UNION ALL
SELECT 'guide_rule', COUNT(*) FROM guide_rule;
