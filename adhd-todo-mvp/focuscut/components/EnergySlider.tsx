'use client';

import { EnergyLevel } from '@/types';

interface EnergySliderProps {
  value: EnergyLevel;
  onChange: (level: EnergyLevel) => void;
}

const LEVELS: { key: EnergyLevel; emoji: string; label: string; desc: string }[] = [
  { key: 'low', emoji: '😴', label: '低', desc: '疲惫，需要小步骤' },
  { key: 'medium', emoji: '🙂', label: '中', desc: '还行，可以干活' },
  { key: 'high', emoji: '⚡', label: '高', desc: '精力充沛，冲！' },
];

export default function EnergySlider({ value, onChange }: EnergySliderProps) {
  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-[var(--text-secondary)]">
        你现在精力怎么样？
      </label>
      <div className="grid grid-cols-3 gap-3">
        {LEVELS.map((level) => (
          <button
            key={level.key}
            type="button"
            onClick={() => onChange(level.key)}
            className={`
              flex flex-col items-center gap-1 rounded-xl p-4 transition-smooth
              border-2
              ${value === level.key
                ? 'border-[var(--accent)] bg-[var(--accent)]/10 scale-105'
                : 'border-[var(--bg-card)] bg-[var(--bg-card)] hover:border-[var(--text-secondary)]'
              }
            `}
          >
            <span className="text-2xl">{level.emoji}</span>
            <span className="text-sm font-semibold">{level.label}</span>
            <span className="text-xs text-[var(--text-secondary)]">{level.desc}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
