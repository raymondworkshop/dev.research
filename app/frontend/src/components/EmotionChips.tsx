const STARTERS = [
  { label: '憤怒', text: '堵车时我很容易暴怒，事后又后悔。' },
  { label: '悲痛', text: '亲人刚去世，悲痛停不下来。' },
  { label: '被冒犯', text: '同事在会议上当众羞辱我。' },
  { label: '焦慮', text: '我很担心别人的评价，做事总怕出错。' },
]

interface Props {
  onSelect: (text: string) => void
  disabled?: boolean
}

export function EmotionChips({ onSelect, disabled }: Props) {
  return (
    <div className="flex flex-wrap justify-center gap-x-4 gap-y-2 pt-4">
      {STARTERS.map((s) => (
        <button
          key={s.label}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(s.text)}
          className="text-sm text-stone-500 hover:text-stone-800 disabled:opacity-40"
        >
          {s.label}
        </button>
      ))}
    </div>
  )
}
