# Expert KB Scraper — SKILL.md

## What This Skill Does

Builds structured Expert Marketing Knowledge Base files from YouTube channels and X/Twitter accounts using Apify. Each expert gets their own `[NAME]_KB.md` file added to the project. The output format matches the Jeremy Haynes KB already in this project.

**Trigger phrases:**
- "add [expert name] to the KB"
- "scrape [expert name]'s YouTube / X"
- "build a KB for [expert name]"
- "continue the KB scraping"
- "pick up where we left off on the KBs"

---

## Actors Used

| Actor | ID | Purpose | Cost |
|---|---|---|---|
| YouTube Channel Video Scraper | `grow_media/youtube-channel-video-scraper` | Get video list from a channel | ~$0.018 per 30 videos |
| YouTube Transcript Scraper | `pintostudio/youtube-transcript-scraper` | Get full transcript per video | $0.01 per video |
| Tweet Scraper V2 | `apidojo/tweet-scraper` | Scrape X/Twitter profile | $0.40 per 1000 tweets |

---

## Full Workflow

### STEP 1 — Get Channel Video List

Run async for each expert channel simultaneously to save time.

```
Actor: grow_media/youtube-channel-video-scraper
Mode: async = true (run in parallel for multiple experts)

Input options:
  channelHandle: "@HandleName"   ← preferred
  channelId: "UCxxxxxxxx"        ← fallback if handle fails (0 results = wrong handle)
  maxResults: 30
  videoType: "long"
  sortOrder: "popular"           ← most viewed first = best signal
```

**Finding channel IDs when handles fail:**
- Search: `"youtube.com/@" "[Expert Name]"` on web
- Check vidiq.com/youtube-stats/channel/[channelId]
- Try common handle variations: `@FirstLast`, `@firstname`, `@BrandName`

**Checking run status:**
```
Actor: get-actor-run
Input: runId from the async call
Look for: status = "SUCCEEDED" and chargedEventCounts > 0
If chargedEventCounts = 0 → handle/ID was wrong, retry with alternative
```

---

### STEP 2 — Review Video List and Pick Top 10

```
Actor: get-actor-output
Input: datasetId from the completed run
Fields: "title,url,viewCount,duration"
Limit: 30
```

**Selection criteria — pick 10 videos that:**
- Are clearly tactical/educational (not vlogs, interviews, or lifestyle)
- Cover distinct topics (don't pick 5 videos all on the same subject)
- Have high view counts relative to the channel average
- Are 10-60 minutes long (sweet spot for transcript depth)
- Avoid: podcasts where the expert isn't the main speaker, pure motivation content

**Expert-specific filters:**
- **Hormozi:** skip gym/fitness content, focus on offer, sales, and business frameworks
- **Suby:** focus on copywriting, VSLs, paid ads — his older content is often better
- **Ravi Abuvala:** focus on YouTube lead machine, call funnels, organic acquisition
- **Sam Ovens:** channel largely dormant post-2022; pick his top 8-10 all-time classics
- **Russell Brunson:** focus on funnel strategy, offers, traffic — not ClickFunnels software tutorials

---

### STEP 3 — Scrape Transcripts (One at a Time)

```
Actor: pintostudio/youtube-transcript-scraper
Mode: sync (wait for result)

Input:
  videoUrl: "https://www.youtube.com/watch?v=VIDEO_ID"
  targetLanguage: "en"
```

Run one at a time. Each takes ~5-10 seconds. For 10 videos = ~2 minutes total.

**Output field to use:** `transcript` — contains the full text

**If transcript returns empty:** the video has auto-captions disabled. Skip it and use the next video on the list.

---

### STEP 4 — Summarise Transcripts into KB Format

After collecting all transcripts, pass them to Claude with this prompt:

```
DISTILLATION PROMPT:

You are building a structured Expert Knowledge Base from YouTube video transcripts.
The expert is: [EXPERT NAME]
Their focus area is: [FOCUS]

I will provide you with [N] video transcripts. For each transcript:
1. Identify the core concept / main framework being taught
2. Extract 4-6 specific tactical takeaways with enough detail to be actionable
3. Note 2-3 direct quotes that capture the key idea
4. Write an "Apply When" section describing when to use this framework

Format each video as a section using this template:

---
TITLE: [Video Title]
VIDEO: [YouTube URL]
CATEGORY: [Category — e.g. Offers / Ads / Sales / Funnels / Messaging]
---

CORE CONCEPT:
[2-3 sentence summary of the main idea]

TACTICAL TAKEAWAYS:
- [Specific tactic with enough context to use]
- [...]

KEY QUOTES:
- "[Direct quote]"

APPLY WHEN:
[1-2 sentences on when/why to reference this]

---

After all videos, add:
- A QUICK REFERENCE section with key benchmarks/numbers mentioned
- A SIGNAL RATING (1-10) and BEST FOR summary for the expert overall

Transcripts follow:
[PASTE TRANSCRIPTS]
```

---

### STEP 5 — Save as Project File

Save output as: `/[FIRSTNAME_LASTNAME]_KB.md`

File naming convention:
```
JEREMY_HAYNES_KB.txt          ← already exists (original format)
X_EXPERTS_KB.md               ← already exists (3 X accounts)
ALEX_HORMOZI_KB.md            ← to be created
SABRI_SUBY_KB.md              ← to be created
RAVI_ABUVALA_KB.md            ← to be created
SAM_OVENS_KB.md               ← to be created
RUSSELL_BRUNSON_KB.md         ← to be created (replaces Dan Kennedy)
```

Then add to project as a Project File so it's available in every conversation.

---

### STEP 6 (Optional) — X/Twitter Scrape

For experts with strong X presence (supplement to YouTube):

```
Actor: apidojo/tweet-scraper
Input:
  twitterHandles: ["handle1", "handle2", "handle3"]  ← up to 3 at once
  maxItems: 200-300 per account
  sort: "Latest"
  tweetLanguage: "en"
```

**Filtering after scrape:**
- Remove: retweets (isRetweet: true), promotional posts, one-liners under 100 chars
- Keep: threads with frameworks, tactical breakdowns, case studies
- Signal-to-noise varies widely — X is lower depth than YouTube, treat as supplementary

---

## COMPLETED EXPERTS (March 2026)

| Expert | Handle / Channel ID | KB File | Videos | Notes |
|---|---|---|---|---|
| Jeremy Haynes | @JeremyHaynes | `JEREMY_HAYNES_KNOWLEDGE_BASE.txt` | 37 | Original build, different format |
| X Experts | brillaas, lamxnt, theroborourke | `X_EXPERTS_KNOWLEDGE_BASE.md` | — | X/Twitter scrape |
| Alex Hormozi | @AlexHormozi | `ALEX_HORMOZI_KB.md` | 10 | 8.5/10 signal |
| Sabri Suby | @SabriSubyOfficial | `SABRI_SUBY_KB.md` | 10 | 9/10 signal |
| Ravi Abuvala | @RaviAbuvala | `RAVI_ABUVALA_KB.md` | 10 | 8/10 signal |
| Sam Ovens | @SamOvensOfficial | `SAM_OVENS_KB.md` | 10 | 8/10 signal |
| Russell Brunson | @RussellBrunson | `RUSSELL_BRUNSON_KB.md` | 10 | 7/10 signal |

### Lessons Learned
- Sabri Suby's handle is `@SabriSubyOfficial` (not `@sabrisuby` or `@SabriSuby`)
- Russell Brunson's handle `@RussellBrunson` works; channel ID also works
- Dan Kennedy was considered but replaced by Brunson — Kennedy's channel has poor transcript quality on old content

---

## Quality Checklist Before Saving a KB

- [ ] Each section has a clear CORE CONCEPT (not just a list of tips)
- [ ] Tactical takeaways are specific enough to act on without the video
- [ ] "Apply When" tells you when to reach for this framework during a client problem
- [ ] No filler content — if a video was mostly stories/motivation, note that and skip
- [ ] Cross-references to Haynes KB where frameworks overlap or complement
- [ ] File named consistently: `FIRSTNAME_LASTNAME_KB.md`

---

## Common Issues and Fixes

| Problem | Cause | Fix |
|---|---|---|
| 0 results from channel scraper | Wrong handle format | Try `@handle` vs handle without @; look up channel ID |
| Transcript returns empty | Auto-captions disabled | Skip video, pick next on list |
| Transcript is garbled/incoherent | Auto-generated captions on heavily accented speaker | Use it anyway but note quality in KB |
| Expert's content is too broad | Channel covers many topics | Be aggressive with filtering in Step 2 — only marketing/business tactics |
| Too much overlap with Haynes KB | Same frameworks covered | Still include — note cross-reference, it validates the framework |
