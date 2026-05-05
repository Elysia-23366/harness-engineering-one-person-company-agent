'use client';

import { useState, useRef, useEffect } from 'react';

interface TaskInputProps {
  onSubmit: (task: string) => void;
  disabled?: boolean;
}

export default function TaskInput({ onSubmit, disabled }: TaskInputProps) {
  const [text, setText] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!disabled) {
      inputRef.current?.focus();
    }
  }, [disabled]);

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-[var(--text-secondary)]">
        你想做什么？说出来就好
      </label>
      <textarea
        ref={inputRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder="例如：写毕业论文、整理房间、准备面试..."
        rows={3}
        maxLength={500}
        className="w-full rounded-xl bg-[var(--bg-card)] border-2 border-transparent
          p-4 text-base text-[var(--text-primary)] placeholder:text-[var(--text-secondary)]
          focus:border-[var(--accent)] focus:outline-none resize-none transition-smooth
          disabled:opacity-50"
      />
      <div className="flex items-center justify-between">
        <span className="text-xs text-[var(--text-secondary)]">
          {text.length}/500 · Enter 发送
        </span>
        <button
          onClick={handleSubmit}
          disabled={disabled || !text.trim()}
          className="rounded-xl bg-[var(--accent)] px-6 py-3 text-sm font-semibold
            text-[var(--bg-primary)] hover:bg-[var(--accent-hover)]
            disabled:opacity-40 disabled:cursor-not-allowed transition-smooth"
        >
          拆解任务 ✂️
        </button>
      </div>
    </div>
  );
}
