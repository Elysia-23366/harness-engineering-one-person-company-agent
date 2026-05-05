/**
 * FocusCut MVP - 核心类型定义
 * 所有数据模型在此统一声明，前端和 API 共用
 */

/** 精力状态：低 / 中 / 高 */
export type EnergyLevel = 'low' | 'medium' | 'high';

/** 单条子任务 */
export interface Subtask {
  id: string;
  action: string;           // 动词开头的可执行指令
  estimated_minutes: number; // 预估耗时（分钟）
  completed: boolean;
}

/** 用户输入的原始任务 */
export interface Task {
  id: string;
  title: string;            // 用户原始输入
  energyLevel: EnergyLevel;
  subtasks: Subtask[];
  createdAt: number;        // Date.now() 时间戳
  completedAt?: number;     // 全部子任务完成的时间戳
}

/** Claude API 请求体 */
export interface DecomposeRequest {
  task: string;
  energyLevel: EnergyLevel;
}

/** Claude API 响应体 */
export interface DecomposeResponse {
  subtasks: Omit<Subtask, 'completed'>[];
}

/** 页面状态机 */
export type AppState =
  | 'idle'          // 初始/空状态
  | 'input'         // 正在输入任务
  | 'decomposing'   // AI 拆解中（loading）
  | 'focusing'      // 聚焦模式（一次看一条）
  | 'complete';     // 全部完成
