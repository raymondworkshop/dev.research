## Study Operating Manual
Personal KB: read → notes → wiki → apply.

### Folders
| Path | Who | Role |
|------|-----|------|
| `notes/` | you | Never modify |
| `books/` | you | Full text for cites |
| `wiki/` | AI | Curated theme pages (not a highlight dump) |
| `outputs/` | AI | Long reports |

### Rules
- Sources of truth: `notes/` + `books/`.
- Wiki: strip `[info]`/`[insights]`/`[how]`; file author meaning cleanly.
- AI prose (intros, merges, framing, study-partner plans): prefix `[AI Synthesis]:` on that line.
- Cite only that note’s `#### reference` (prefer `books/…`). No summaries/quizzes unless asked.

### Signals (compile/study only — do not copy into wiki)
| Mark | Use |
|------|-----|
| `###` / green | theme (strong) |
| `**bold**` / purple, `[insights]` / pink | theme *suggestion* (merge/skip OK) |
| `[how]` / blue | → `### Actions` / study-partner try |
| `[info]` / yellow | detail under a theme, not a new page |

### Pipeline
1. **Export** — `make books-export BOOK='title|id'` · `LIST=1`. Colors → table above (merge paras; `##` chapters; green→`###`).

2. **Compile** — `notes/` → `wiki/<theme>.md`  
   Prefer `###` pages; bold/insights = suggestions (group/rename/drop). `[how]` → plain Actions bullets.  
   Template: `[AI Synthesis]:` intro → `###` → `### Actions` → `## Sources` → `## Related Topics`  
   **Default:** agent picks themes (merge `wiki/INDEX.md`), writes pages, updates INDEX. Skip one-shot full-note `make sync` on large notes (token cutoff).  
   **Optional draft:** `make sync NOTE='…' THEMES='one' DRY=1` → `outputs/sync-draft/` → agent merges into `wiki/` + INDEX.

3. **Study partner** — real issue + note/`#### reference` only. One `[how]` to try + `[AI Synthesis]:` plan · 1–2 questions.

4. **Query** — `wiki/INDEX.md`: Summary → Findings → Evidence → Recommendations. Complex → `outputs/`.

5. **Audit** — orphans, bad `[[links]]`, contradictions. `make audit`.
