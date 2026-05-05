'use client';

import { Task } from '@/types';

interface FocusViewProps {
  task: Task;
  currentSubtaskIndex: number;
  onToggle: (subtaskId: string) => void;
  onNext: () => void;
  onExit: () => void;
}

export default function FocusView({
  task,
  currentSubtaskIndex,
  onToggle,
  onNext,
  onExit,
}: FocusViewProps) {
  const current = task.subtasks[currentSubtaskIndex];
  const completedCount = task.subtasks.filter((s) => s.completed).length;
  const totalCount = task.subtasks.length;
  const progress = (completedCount / totalCount) * 100;

  if (!current) {
    return (
      <div className="flex flex-col items-center justify-center gap-6 py-16 text-center">
        <span className="text-6xl">🎉</span>
        <h2 className="text-2xl font-bold">全部完成！</h2>
        <p className="text-[var(--text-secondary)]">
          「{task.title}」的所有步骤都搞定了
        </p>
        <button
          onClick={onExit}
          className="rounded-xl bg-[var(--accent)] px-6 py-3 font-semibold
            text-[var(--bg-primary)] hover:bg-[var(--accent-hover)] transition-smooth"
        >
          返回
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 进度条 */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-[var(--text-secondary)]">
          <span>{task.title}</span>
          <span>{completedCount}/{totalCount}</span>
        </div>
        <div className="h-2 rounded-full bg-[var(--bg-card)] overflow-hidden">
          <div
            className="h-full rounded-full bg-[var(--accent)] transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* 当前子任务卡片 */}
      <div className="rounded-2xl bg-[var(--bg-card)] p-8 text-center space-y-6">
        <div className="space-y-2">
          <span className="text-xs text-[var(--text-secondary)]">
            步骤 {currentSubtaskIndex + 1} / {totalCount}
          </span>
          <h2 className="text-xl font-bold leading-relaxed">
            {current.action}
          </h2>
          <span className="inline-block rounded-full bg-[var(--accent)]/10
            px-3 py-1 text-xs text-[var(--accent)]">
            预估 {current.estimated_minutes} 分钟
          </span>
        </div>

        <div className="flex flex-col gap-3">
          <button
            onClick={() => {
              onToggle(current.id);
              onNext();
            }}
            className="w-full rounded-xl bg-[var(--success)] px-6 py-4 text-lg
              font-bold text-[var(--bg-primary)] hover:opacity-90 transition-smooth"
          >
            ✅ 搞定了！
          </button>
          <button
            onClick={onNext}
            className="w-full rounded-xl bg-[var(--bg-primary)] border-2
              border-[var(--text-secondary)] px-6 py-3 text-sm
              text-[var(--text-secondary)] hover:border-[var(--text-primary)]
              hover:text-[var(--text-primary)] transition-smooth"
          >
            先跳过，看下一步 →
          </button>
        </div>
      </div>

      {/* 退出按钮 */}
      <button
        onClick={onExit}
        className="w-full text-center text-sm text-[var(--text-secondary)]
          hover:text-[var(--text-primary)] transition-smooth py-2"
      >
        退出聚焦模式
      </button>
    </div>
  );
}
