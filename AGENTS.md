## My Research Operating Manual  

### Purpose
Research knowledge base for me.
Used for: emotion or decision support, awareness, personal learning,  and content research.  

### My Research Context
- Topic: Stoicism 
- Goal: Build a comprehensive, interconnected wiki on Stoicism, covering key concepts, figures, texts, and modern applications. Use this wiki to support my personal learning and content creation on the topic.
- Sources: A mix of classic texts (e.g., Meditations), modern interpretations (e.g., The Daily Stoic), and relevant articles or reports I find over time.  


### Structure Rules  
- raw/ contains unprocessed source material. Never modify raw files.
- wiki/ is the organized knowledge base. AI maintains this entirely.
- outputs/ stores generated reports and analysis.


### Agent Skills & Workflows
#### 1. Compile (raw -> wiki)
- Scan for any new or modified source in `raw/` and the existing wiki pages.
    - update any existing pages affected by the new csource
    - create new entity pages for any new topics introduced
    - Use `[[wiki links]]` for cross-references
    - Flag any contradiction with previously compiled knowledge
    - Update `wiki/INDEX.md`
    - Match the input language perfectly
    - **Wiki page template:** intro → `###` sections → `## Sources` table (daily_stoic / meditations / raw_summary) → `## Related Topics`
    - `raw/` = summaries; `books/` = authoritative Stoic detail — Sources should point to books first  

#### 2. Audit
- orphan pages: pages that no other page links to   
- missing pages: concepts referenced with [[brackets]] that dont have their own page yet 
- contradictions: claims that conflicts across pages
- stale claims: things that may have been superseded by a more recent source in raw/ suggest fixes and, where confident, apply them directly

#### 3. Query
- To answer questions, navigate via `wiki/INDEX.md` -> Specific Articles.
- Summary (3 sentences)  → Key Findings → Supporting Evidence → Recommendations.  
- Save complex query results to `outputs/`.
