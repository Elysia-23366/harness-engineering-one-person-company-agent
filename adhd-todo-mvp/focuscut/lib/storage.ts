/**
 * localStorage 封装
 * MVP 阶段无账号体系，所有数据存浏览器本地
 */

import { Task } from '@/types';

const STORAGE_KEY = 'focuscut_tasks';

/** 读取全部任务 */
export function getTasks(): Task[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    console.error('[storage] Failed to parse tasks from localStorage');
    return [];
  }
}

/** 保存全部任务（全量覆写） */
export function saveTasks(tasks: Task[]): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
  } catch {
    console.error('[storage] Failed to save tasks to localStorage');
  }
}

/** 追加一条任务 */
export function addTask(task: Task): void {
  const tasks = getTasks();
  tasks.unshift(task); // 最新的在前面
  saveTasks(tasks);
}

/** 更新指定任务 */
export function updateTask(taskId: string, updates: Partial<Task>): void {
  const tasks = getTasks();
  const idx = tasks.findIndex(t => t.id === taskId);
  if (idx !== -1) {
    tasks[idx] = { ...tasks[idx], ...updates };
    saveTasks(tasks);
  }
}

/** 切换子任务完成状态 */
export function toggleSubtask(taskId: string, subtaskId: string): Task | null {
  const tasks = getTasks();
  const task = tasks.find(t => t.id === taskId);
  if (!task) return null;

  const sub = task.subtasks.find(s => s.id === subtaskId);
  if (!sub) return null;

  sub.completed = !sub.completed;

  // 检查是否全部完成
  const allDone = task.subtasks.every(s => s.completed);
  if (allDone && !task.completedAt) {
    task.completedAt = Date.now();
  } else if (!allDone) {
    task.completedAt = undefined;
  }

  saveTasks(tasks);
  return task;
}

/** 删除指定任务 */
export function deleteTask(taskId: string): void {
  const tasks = getTasks().filter(t => t.id !== taskId);
  saveTasks(tasks);
}

/** 清空所有数据 */
export function clearAll(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(STORAGE_KEY);
}
