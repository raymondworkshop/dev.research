# My Research Operating Manual  

## Purpose
Research knowledge base for me.
Used for: personal learning, awareness, emotion or decision support, and content research.  

## My Research Context
- Topic: Stoicism 
- Goal: Build a comprehensive, interconnected wiki on Stoicism, covering key concepts, figures, texts, and modern applications. Use this wiki to support my personal learning and content creation on the topic.
- Sources: A mix of classic texts (e.g., Meditations), modern interpretations (e.g., The Daily Stoic), and relevant articles or reports I find over time.  


## Structure Rules  
- raw/ contains unprocessed source material. Never modify raw files.
- wiki/ is the organized knowledge base. AI maintains this entirely.
- outputs/ stores generated reports and analysis.

## Commands
- **Sync Wiki**: When the prompt "update wiki/ based on raw/ and GEMINI.md" is received, the AI must:
    1. Scan the `raw/` directory for any new or modified files.
    2. Process the content of these files into individual topic pages in `wiki/` following the [[Wiki Standards]].
    3. Update `wiki/INDEX.md` alphabetically to reflect all current topics.
    4. Provide an Executive Summary of the updates performed.
 

## Wiki Standards
- One topic per file in wiki/  
- Every file starts with a 2-sentence summary
- Related topics linked using [[topic-name]] format
- INDEX.md maintained alphabetically, updated with every change
- When new raw sources arrive, update all relevant wiki articles
- Never translate the source language. Match the output language to the input language perfectly
- Flag contradictions between sources immediately

## Lint
Review the entire wiki/ directory. Complete this audit:
- Flag contradictions between articles
- Find topics mentioned but never fully explained
- List claims not backed by a source in raw/
- Identify stale information (>90 days without update)
- Suggest 3 new articles to fill knowledge gaps



## Output Format  
When I ask for a report: Executive Summary (3 sentences)  → Key Findings → Supporting Evidence → Recommendations.  
When I ask for a recommendation: Context → Options (max 3) → Recommendation → Next Step.