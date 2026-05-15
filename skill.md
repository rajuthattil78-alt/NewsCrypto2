# TELEGRAM BOT COMPLIANCE SKILL

---

## 1. CORE PRINCIPLES

* Moderation evaluates full user journey (ad → bot → UX → behavior)
* Clean ad + aggressive funnel = rejection or account restriction
* Moderation system = hybrid:

  * automated NLP filtering (text, formatting, links)
  * automated crawler (destination scan)
  * human review (UX quality, intent, “vibe”)
* Rule 4.1 (Destination Quality) = primary rejection weapon (subjective)
* Rule 4.2 (Functionality) = technical completeness requirement
* Bots must be instantly interactive (zero friction)
* Trust score determines approval speed and depth of review
* New accounts = stricter scrutiny
* Agency-backed accounts = faster approvals
* Deterministic ad system (ads shown to all users in channel) → strict quality control

---

## 2. BOT TYPE RISK MATRIX

### Utility / Automation Bots

* approval_probability: very high
* risk_level: 1
* allowed_if: instant response, clear function
* reject_if: slow response, broken UI
* notes: safest category

### AI Bots

* approval_probability: high
* risk_level: 3
* allowed_if: unique UX, structured output, branding
* reject_if: raw API wrapper
* notes: onboarding quality critical

### Crypto Bots

* approval_probability: low (official ads)
* risk_level: 8.5
* allowed_if: framed as analytics / monitoring / tools
* reject_if: profit language or trading promises
* notes: extremely sensitive

### Trading Bots

* approval_probability: very low
* risk_level: 9
* allowed_if: simulation / automation explanation
* reject_if: profit or return claims
* notes: must avoid financial promises completely

### SaaS Bots

* approval_probability: high
* risk_level: 2.5
* allowed_if: demo mode accessible
* reject_if: login wall at entry
* notes: must work instantly

### Gaming / Mini Apps

* approval_probability: medium-high
* risk_level: 4
* allowed_if: fast, mobile optimized
* reject_if: loading delays, UI issues
* notes: performance critical

### Affiliate Bots

* approval_probability: medium-low
* risk_level: 6.5
* allowed_if: real utility (quiz, comparison, tools)
* reject_if: link dumping
* notes: must hide monetization intent

### Education Bots

* approval_probability: high
* risk_level: 3
* allowed_if: immediate free value
* reject_if: fake free → paywall
* notes: highly favored

### VPN / Privacy Bots

* approval_probability: low
* risk_level: 7.5
* allowed_if: enterprise security framing
* reject_if: censorship bypass messaging
* notes: geo-sensitive

### E-commerce Bots

* approval_probability: high
* risk_level: 3.5
* allowed_if: clear payment + refund policy
* reject_if: restricted products
* notes: must include support

### Media / Download Bots

* approval_probability: medium
* risk_level: 5.5
* allowed_if: framed as storage/tool
* reject_if: piracy keywords
* notes: sensitive to copyright

### Finance (Non-Crypto)

* approval_probability: low
* risk_level: 8
* allowed_if: tracking / budgeting only
* reject_if: lending or returns
* notes: data handling important

### NSFW Bots

* approval_probability: zero
* risk_level: 10
* reject_if: any adult signal
* notes: never use ads

---

## 3. HARD COMPLIANCE RULES

* MUST use Telegram-native destinations only (t.me / @username)
* MUST NOT use external links in ad copy
* MUST NOT use URL shorteners or IP links
* MUST have:

  * high-resolution avatar
  * complete bio/description
* MUST NOT use:

  * profanity
  * masked vulgarity
  * slurs
* MUST NOT use:

  * ALL CAPS
  * spaced text (s a l e)
  * ASCII art
* MUST NOT include line breaks or lists in ad text
* MUST NOT promise:

  * profits
  * guaranteed results
  * earnings
* MUST NOT promote:

  * MLM / pyramid
  * gambling / adult / illegal content
* MUST ensure destination works perfectly

---

## 4. SOFT SIGNAL OPTIMIZATION

* Use branded, clean usernames
* Avoid random strings or numbers
* Remove “test”, “demo” from public identity
* Ensure perfect grammar and spelling
* Implement full localization for target regions
* Maintain channel history ≥ 14–30 days
* Maintain realistic engagement ratios
* Use consistent branding (colors, tone)
* Store data securely (Telegram APIs preferred)

---

## 5. BOT STRUCTURE BLUEPRINT

* /start must respond instantly
* First message must clearly state value
* No wall of text
* Use progressive disclosure:

  * reveal features step-by-step
* Use inline keyboards (preferred over commands)
* Provide:

  * /privacy
  * /terms
* Ensure all buttons work
* No dead links or empty screens
* High-risk elements must be deep in flow

---

## 6. SAFE CONTENT GENERATION RULES

* tone: neutral, factual, professional
* avoid emotional or hype language
* banned phrases:

  * Buy now
  * Click here
  * Best
  * #1
  * Guaranteed
  * Risk-free
  * 100x
* safe replacements:

  * Explore features
  * View data
  * Analyze trends
  * Monitor activity
* formatting:

  * sentence case only
* emojis:

  * max 1–2
  * no 🚀 🚨 spam

---

## 7. AD COPY RULESET

* max length: 160 characters
* no imperative commands
* no hype or exaggerated claims
* use curiosity-based phrasing
* grammar must be perfect
* no line breaks
* include max 1 Telegram internal link
* match ad promise with bot functionality

---

## 8. REJECTION TRIGGERS

### Explicit

* adult, gambling, illegal products
* deceptive finance

### Hidden

* missing translations
* incomplete profiles
* poor UX

### Pattern-based

* reused creatives from banned ads
* cloned bot structures

### Behavioral

* aggressive upsell immediately after click

### Technical

* slow response
* errors
* paywall at entry

---

## 9. TRUST SIGNAL ENGINE

### Builds trust

* aged accounts
* Telegram Premium
* consistent IP usage
* agency funding

### Reduces trust

* VPN hopping
* burner accounts
* no history
* sudden scaling

### Stability

* 30-day warmup
* consistent activity
* controlled growth

---

## 10. BUILD CHECKLIST (FINAL GATE)

* [ ] /start instant response
* [ ] no errors anywhere
* [ ] avatar high quality
* [ ] bio complete
* [ ] no profit language
* [ ] ad < 160 chars
* [ ] no imperatives
* [ ] no banned content
* [ ] no login wall
* [ ] features accessible immediately
* [ ] translations complete

---

## 11. INTENT FRAMING RULES

* ALWAYS describe tool, NEVER outcome
* NEVER imply user will earn, gain, or benefit financially
* convert:

  * trading → analytics
  * earning → monitoring
  * signals → alerts
* focus on:

  * data
  * process
  * insights
* remove all speculative language
* prioritize educational or utility framing

---

## 12. FUNNEL CONTROL RULES

* NO monetization at entry point
* first interaction MUST provide value
* upsell depth ≥ 2–3 steps
* NEVER redirect immediately to external site
* NEVER request payment before demonstrating value
* gradually introduce advanced features
* separate free vs premium clearly

---

## 13. SHADOW-BAN PREVENTION

* DO NOT reuse ad creatives across accounts
* DO NOT duplicate bot structures at scale
* maintain consistent infrastructure (IP, device)
* avoid rapid account creation
* avoid suspicious traffic spikes
* keep unique variations for each campaign
* monitor “In Review” delays → rebuild if stuck

---

## 14. GEO & REGULATORY FILTER

* avoid restricted regions for sensitive niches
* adjust messaging based on region
* avoid:

  * censorship-related wording
  * political implications
* use neutral global positioning
* exclude high-risk jurisdictions when needed

---

## 15. GRAY-ZONE STRATEGY RULES

* operate risky niches under:

  * education
  * analytics
  * tools
* NEVER expose full intent in:

  * ad
  * first interaction
* reveal sensitive features gradually
* keep core layer compliant
* isolate high-risk elements deep in UX
* ensure initial reviewer experience is fully compliant

---
