import type { Lang } from '../lib/i18n'

export type ReplySectionType =
  | 'ack'
  | 'not_control'
  | 'in_control'
  | 'reframe'
  | 'action'
  | 'question'

interface ReplySection {
  type: ReplySectionType
  body: string
}

type DisplayBlock =
  | { kind: 'ack'; body: string }
  | { kind: 'dichotomy'; notControl: string; inControl: string }
  | { kind: 'reframe'; body: string }
  | { kind: 'labeled'; label: string; body: string }

const LABELS: Record<Lang, { action: string; question: string }> = {
  'zh-Hant': {
    action: '今天可做的一件小事',
    question: '想一想',
  },
  'zh-Hans': {
    action: '今天可做的一件小事',
    question: '想一想',
  },
  en: {
    action: 'One small step today',
    question: 'Reflect',
  },
}

const RULES: { type: ReplySectionType; pattern: RegExp }[] = [
  { type: 'ack', pattern: /^(承認情緒|承认情绪)[：:]\s*/i },
  { type: 'ack', pattern: /^Acknowledge:\s*/i },
  { type: 'not_control', pattern: /^(\*\*)?(不可控|不可控制)(\*\*)?[：:]\s*/i },
  { type: 'not_control', pattern: /^(\*\*)?Not in your control(\*\*)?[：:]\s*/i },
  { type: 'in_control', pattern: /^(\*\*)?(可控)(\*\*)?[：:]\s*/i },
  { type: 'in_control', pattern: /^(\*\*)?In your control(\*\*)?[：:]\s*/i },
  { type: 'reframe', pattern: /^(斯多葛重述|斯多葛式重述)[：:]\s*/i },
  { type: 'reframe', pattern: /^Stoic reframe:\s*/i },
  { type: 'action', pattern: /^(今天可做的一件小事|今天可做的小事)[：:]\s*/i },
  { type: 'action', pattern: /^One small step today:\s*/i },
]

function trimClause(text: string): string {
  return text.replace(/[。．.；;、，,]+$/g, '').trim()
}

function stripMarkdownBold(text: string): string {
  return text.replace(/\*\*/g, '')
}

function formatReframe(body: string, lang: Lang): string {
  const text = body.trim().replace(/[。．.]+$/g, '')
  if (lang === 'en') {
    const sentence = text.charAt(0).toLowerCase() + text.slice(1)
    return `From a Stoic perspective, ${sentence}.`
  }
  if (lang === 'zh-Hans') {
    return `从斯多葛的角度看，${text}。`
  }
  return `以斯多葛的角度看，${text}。`
}

function formatDichotomy(notControl: string, inControl: string, lang: Lang): string {
  const nc = trimClause(notControl)
  const ic = trimClause(inControl)
  if (lang === 'en') {
    return `You cannot control “${nc}”, but you can control “${ic}.”`
  }
  if (lang === 'zh-Hans') {
    return `你无法控制「${nc}」，但你可以控制「${ic}」。`
  }
  return `你無法控制「${nc}」，但你可以控制「${ic}」。`
}

function parseSections(text: string): ReplySection[] | null {
  const normalized = stripMarkdownBold(text).trim()
  if (!normalized) return null

  const blocks = normalized.split(/\n\n+/).map((b) => b.trim()).filter(Boolean)
  if (blocks.length < 2) return null

  const sections: ReplySection[] = []

  for (const block of blocks) {
    let matched = false
    for (const rule of RULES) {
      if (rule.pattern.test(block)) {
        if (rule.type === 'not_control' && /^不可控[：:]/.test(block) && /\n可控[：:]/.test(block)) {
          const lines = block.split(/\n/)
          const nc = lines[0].replace(/^(\*\*)?不可控(\*\*)?[：:]\s*/, '').trim()
          const ic = lines
            .slice(1)
            .join('\n')
            .replace(/^(\*\*)?可控(\*\*)?[：:]\s*/, '')
            .trim()
          sections.push({ type: 'not_control', body: nc })
          sections.push({ type: 'in_control', body: ic })
        } else if (
          rule.type === 'not_control' &&
          /^Not in your control:/i.test(block) &&
          /\nIn your control:/i.test(block)
        ) {
          const lines = block.split(/\n/)
          const nc = lines[0].replace(/^Not in your control:\s*/i, '').trim()
          const ic = lines.slice(1).join('\n').replace(/^In your control:\s*/i, '').trim()
          sections.push({ type: 'not_control', body: nc })
          sections.push({ type: 'in_control', body: ic })
        } else {
          sections.push({ type: rule.type, body: block.replace(rule.pattern, '').trim() })
        }
        matched = true
        break
      }
    }
    if (!matched) {
      sections.push({ type: 'question', body: block })
    }
  }

  const hasCore = sections.some((s) => s.type === 'not_control' || s.type === 'in_control')
  return hasCore ? sections : null
}

function toDisplayBlocks(sections: ReplySection[], lang: Lang): DisplayBlock[] {
  const L = LABELS[lang]
  const blocks: DisplayBlock[] = []

  for (let i = 0; i < sections.length; i++) {
    const s = sections[i]
    if (s.type === 'ack') {
      blocks.push({ kind: 'ack', body: s.body })
    } else if (s.type === 'not_control' && sections[i + 1]?.type === 'in_control') {
      blocks.push({
        kind: 'dichotomy',
        notControl: s.body,
        inControl: sections[i + 1].body,
      })
      i++
    } else if (s.type === 'reframe') {
      blocks.push({ kind: 'reframe', body: s.body })
    } else if (s.type === 'action') {
      blocks.push({ kind: 'labeled', label: L.action, body: s.body })
    } else if (s.type === 'question') {
      blocks.push({ kind: 'labeled', label: L.question, body: s.body })
    }
  }

  return blocks
}

function SectionLabel({ children }: { children: string }) {
  return (
    <p className="mb-1 text-[11px] font-semibold tracking-wide text-stone-500">{children}</p>
  )
}

interface Props {
  content: string
  lang: Lang
  streaming?: boolean
}

export function StructuredReply({ content, lang, streaming }: Props) {
  const sections = !streaming ? parseSections(content) : null
  const blocks = sections ? toDisplayBlocks(sections, lang) : null
  const L = LABELS[lang]

  if (!blocks) {
    return <p className="whitespace-pre-wrap leading-relaxed">{content}</p>
  }

  return (
    <div className="space-y-3.5">
      {blocks.map((block, i) => {
        if (block.kind === 'ack') {
          return (
            <p key={i} className="leading-relaxed text-stone-800">
              {block.body}
            </p>
          )
        }
        if (block.kind === 'dichotomy') {
          return (
            <p key={i} className="leading-relaxed text-stone-800">
              {formatDichotomy(block.notControl, block.inControl, lang)}
            </p>
          )
        }
        if (block.kind === 'reframe') {
          return (
            <p key={i} className="leading-relaxed text-stone-800">
              {formatReframe(block.body, lang)}
            </p>
          )
        }
        return (
          <div key={i} className={block.label === L.question ? 'border-t border-stone-100 pt-3' : undefined}>
            <SectionLabel>{block.label}</SectionLabel>
            <p className="leading-relaxed text-stone-800">{block.body}</p>
          </div>
        )
      })}
    </div>
  )
}
