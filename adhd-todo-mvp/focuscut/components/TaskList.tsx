'use client';

import { Task } from '@/types';

interface TaskListProps {
  tasks: Task[];
  onResume: (task: Task) => void;
  onDelete: (taskId: string) => void;
}

export default function TaskList({ tasks, onResume, onDelete }: TaskListProps) {
  if (tasks.length === 0) {
    return (
      <div className="text-center py-12 text-[var(--text-secondary)]">
        <span className="text-4xl block mb-4">📋</span>
        <p>还没有任务，输入一个开始吧</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-[var(--text-secondary)]">
        历史任务 ({tasks.length})
      </h3>
      {tasks.map((task) => {
        const completedCount = task.subtasks.filter((s) => s.completed).length;
        const totalCount = task.subtasks.length;
        const isComplete = completedCount === totalCount;

        return (
          <div
            key={task.id}
            className="rounded-xl bg-[var(--bg-card)] p-4 space-y-2"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <h4 className={`font-medium truncate ${isComplete ? 'line-through text-[var(--text-secondary)]' : ''}`}>
                  {isComplete && '✅ '}{task.title}
                </h4>
                <p className="text-xs text-[var(--text-secondary)] mt-1">
                  {completedCount}/{totalCount} 步完成 · 精力{
                    task.energyLevel === 'low' ? '低' :
                    task.energyLevel === 'medium' ? '中' : '高'
                  }
                </p>
              </div>
              <div className="flex gap-2 shrink-0">
                {!isComplete && (
                  <button
                    onClick={() => onResume(task)}
                    className="rounded-lg bg-[var(--accent)]/10 px-3 py-1.5
                      text-xs font-medium text-[var(--accent)]
                      hover:bg-[var(--accent)]/20 transition-smooth"
                  >
                    继续
                  </button>
                )}
                <button
                  onClick={() => onDelete(task.id)}
                  className="rounded-lg bg-[var(--danger)]/10 px-3 py-1.5
                    text-xs font-medium text-[var(--danger)]
                    hover:bg-[var(--danger)]/20 transition-smooth"
                >
                  删除
                </button>
              </div>
            </div>
            {/* 子任务进度条 */}
            <div className="h-1.5 rounded-full bg-[var(--bg-primary)] overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  isComplete ? 'bg-[var(--success)]' : 'bg-[var(--accent)]'
                }`}
                style={{ width: `${(completedCount / totalCount) * 100}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
