'use client';

import { useState } from 'react';
import { Subtask } from '@/types';

interface SubtaskEditorProps {
  subtasks: Omit<Subtask, 'completed'>[];
  onConfirm: (subtasks: Omit<Subtask, 'completed'>[]) => void;
  onCancel: () => void;
}

export default function SubtaskEditor({ subtasks: initial, onConfirm, onCancel }: SubtaskEditorProps) {
  const [subtasks, setSubtasks] = useState(initial);

  const updateAction = (id: string, action: string) => {
    setSubtasks((prev) =>
      prev.map((s) => (s.id === id ? { ...s, action } : s))
    );
  };

  const removeSubtask = (id: string) => {
    setSubtasks((prev) => prev.filter((s) => s.id !== id));
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-[var(--text-secondary)]">
          调整步骤（可选）
        </h3>
        <span className="text-xs text-[var(--text-secondary)]">
          {subtasks.length} 步
        </span>
      </div>

      <div className="space-y-2">
        {subtasks.map((sub, i) => (
          <div key={sub.id} className="flex items-center gap-2">
            <span className="text-xs text-[var(--text-secondary)] w-6 text-right shrink-0">
              {i + 1}.
            </span>
            <input
              value={sub.action}
              onChange={(e) => updateAction(sub.id, e.target.value)}
              className="flex-1 rounded-lg bg-[var(--bg-card)] border border-transparent
                px-3 py-2 text-sm text-[var(--text-primary)]
                focus:border-[var(--accent)] focus:outline-none transition-smooth"
            />
            <button
              onClick={() => removeSubtask(sub.id)}
              className="text-[var(--danger)] hover:opacity-80 text-sm px-2 transition-smooth"
              title="删除此步骤"
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      <div className="flex gap-3">
        <button
          onClick={onCancel}
          className="flex-1 rounded-xl border-2 border-[var(--text-secondary)]
            py-3 text-sm text-[var(--text-secondary)]
            hover:border-[var(--text-primary)] hover:text-[var(--text-primary)]
            transition-smooth"
        >
          取消
        </button>
        <button
          onClick={() => onConfirm(subtasks)}
          disabled={subtasks.length === 0}
          className="flex-1 rounded-xl bg-[var(--accent)] py-3 text-sm
            font-semibold text-[var(--bg-primary)]
            hover:bg-[var(--accent-hover)]
            disabled:opacity-40 disabled:cursor-not-allowed transition-smooth"
        >
          开始聚焦 →
        </button>
      </div>
    </div>
  );
}
