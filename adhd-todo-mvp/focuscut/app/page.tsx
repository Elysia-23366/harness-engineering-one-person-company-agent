'use client';

import { useState, useCallback, useEffect } from 'react';
import { Task, Subtask, EnergyLevel, AppState, DecomposeResponse } from '@/types';
import { getTasks, addTask, toggleSubtask, deleteTask } from '@/lib/storage';
import EnergySlider from '@/components/EnergySlider';
import TaskInput from '@/components/TaskInput';
import FocusView from '@/components/FocusView';
import TaskList from '@/components/TaskList';
import SubtaskEditor from '@/components/SubtaskEditor';

export default function Home() {
  const [appState, setAppState] = useState<AppState>('idle');
  const [energyLevel, setEnergyLevel] = useState<EnergyLevel>('medium');
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [currentSubtaskIndex, setCurrentSubtaskIndex] = useState(0);
  const [pendingSubtasks, setPendingSubtasks] = useState<Omit<Subtask, 'completed'>[] | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState<string | null>(null);

  // 加载历史任务
  useEffect(() => {
    setTasks(getTasks());
  }, []);

  // 提交任务 → 调 API 拆解
  const handleTaskSubmit = useCallback(async (taskText: string) => {
    setAppState('decomposing');
    setError(null);

    try {
      const res = await fetch('/api/decompose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: taskText, energyLevel }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || 'API request failed');
      }

      const data: DecomposeResponse = await res.json();

      // 给每个子任务加上 id
      const subtaskBases = data.subtasks.map((s, i) => ({
        ...s,
        id: `sub-${Date.now()}-${i}`,
      }));

      const newTask: Task = {
        id: `task-${Date.now()}`,
        title: taskText,
        energyLevel,
        subtasks: subtaskBases.map((s) => ({ ...s, completed: false })),
        createdAt: Date.now(),
      };

      // 进入编辑确认阶段
      setCurrentTask(newTask);
      setPendingSubtasks(subtaskBases);
      setAppState('input');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '未知错误';
      setError(msg);
      setAppState('idle');
    }
  }, [energyLevel]);

  // 确认子任务 → 进入聚焦模式
  const handleConfirmSubtasks = useCallback((edited: Omit<Subtask, 'completed'>[]) => {
    if (!currentTask) return;

    const subtasks: Subtask[] = edited.map((s) => ({
      ...s,
      completed: false,
    }));

    const task: Task = { ...currentTask, subtasks };
    addTask(task);
    setTasks(getTasks());
    setCurrentTask(task);
    setCurrentSubtaskIndex(0);
    setPendingSubtasks(null);
    setAppState('focusing');
  }, [currentTask]);

  // 切换子任务完成
  const handleToggleSubtask = useCallback((subtaskId: string) => {
    if (!currentTask) return;
    const updated = toggleSubtask(currentTask.id, subtaskId);
    if (updated) {
      setCurrentTask(updated);
      setTasks(getTasks());
    }
  }, [currentTask]);

  // 下一条子任务
  const handleNext = useCallback(() => {
    if (!currentTask) return;
    const nextIncomplete = currentTask.subtasks.findIndex(
      (s, i) => i > currentSubtaskIndex && !s.completed
    );
    if (nextIncomplete !== -1) {
      setCurrentSubtaskIndex(nextIncomplete);
    } else {
      setCurrentSubtaskIndex(currentTask.subtasks.length);
    }
  }, [currentTask, currentSubtaskIndex]);

  // 恢复历史任务到聚焦模式
  const handleResume = useCallback((task: Task) => {
    setCurrentTask(task);
    const firstIncomplete = task.subtasks.findIndex(s => !s.completed);
    setCurrentSubtaskIndex(firstIncomplete >= 0 ? firstIncomplete : 0);
    setAppState('focusing');
  }, []);

  // 删除任务
  const handleDelete = useCallback((taskId: string) => {
    deleteTask(taskId);
    setTasks(getTasks());
  }, []);

  // 退出聚焦
  const handleExit = useCallback(() => {
    setCurrentTask(null);
    setCurrentSubtaskIndex(0);
    setAppState('idle');
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <header className="text-center space-y-1">
        <h1 className="text-2xl font-bold">
          ✂️ FocusCut
        </h1>
        <p className="text-sm text-[var(--text-secondary)]">
          大任务 → 小步骤 → 一次一步
        </p>
      </header>

      {/* Error banner */}
      {error && (
        <div className="rounded-xl bg-[var(--danger)]/10 border border-[var(--danger)]/30 p-4 text-sm text-[var(--danger)]">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 underline"
          >
            关闭
          </button>
        </div>
      )}

      {/* 聚焦模式 */}
      {appState === 'focusing' && currentTask && (
        <FocusView
          task={currentTask}
          currentSubtaskIndex={currentSubtaskIndex}
          onToggle={handleToggleSubtask}
          onNext={handleNext}
          onExit={handleExit}
        />
      )}

      {/* 子任务编辑确认 */}
      {appState === 'input' && pendingSubtasks && (
        <SubtaskEditor
          subtasks={pendingSubtasks}
          onConfirm={handleConfirmSubtasks}
          onCancel={() => {
            setPendingSubtasks(null);
            setCurrentTask(null);
            setAppState('idle');
          }}
        />
      )}

      {/* 输入模式 */}
      {appState === 'idle' && (
        <>
          <EnergySlider value={energyLevel} onChange={setEnergyLevel} />
          <TaskInput onSubmit={handleTaskSubmit} disabled={false} />
        </>
      )}

      {/* Loading */}
      {appState === 'decomposing' && (
        <div className="flex flex-col items-center gap-4 py-12">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-[var(--accent)] border-t-transparent" />
          <p className="text-sm text-[var(--text-secondary)]">
            正在拆解任务...
          </p>
        </div>
      )}

      {/* 历史任务列表 */}
      {appState === 'idle' && (
        <TaskList
          tasks={tasks}
          onResume={handleResume}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
}
