# SPAIN V3 CONTENT PLAN

Status: CONTENT DESIGN / VISUALS PENDING  
Working branch: `country/spain`  
Purpose: Pilot the revised JOURNEY ATLAS Country Page standard before applying it to other countries.

## 1. Locked principles

- Primary goal: make the reader interested in Spain and want to go there.
- Do not turn the page into a guidebook.
- Scene selection starts from "what should the reader discover about this country?", not regional coverage.
- Regional / terrain dispersion is a final balancing condition, not a reason to include a weak scene.
- Every scene must pass both gates:
  1. I want to see this place in person.
  2. This scene adds a meaningful understanding or discovery of Spain.
- A scene that is informative but does not create travel desire is not selected.

## 2. Hero

- Granada / Alhambra from Mirador de San Nicolás
- STATE: APPROVED / KEEP
- Role: strongest visual entrance into Spain; Islamic heritage + city + Sierra Nevada context.
- Do not repeat the Hero inside the 8 Scenes unless a future content reason clearly justifies it.

## 3. Revised 8 Scenes

| No. | Place | Role | State | Why it belongs |
|---|---|---|---|---|
| 01 | Barcelona / Turó de la Rovira | ANCHOR + ATLAS VIEW | APPROVED / KEEP | The grid of Eixample, landmarks and Mediterranean geography can be read in one view. |
| 02 | San Sebastián / La Concha | ATLAS VIEW | APPROVED / KEEP | Shows the green Atlantic Spain that contrasts with the common dry-Mediterranean image. |
| 03 | Picos de Europa / Picu Urriellu | DISCOVERY | APPROVED / KEEP | A dramatic limestone mountain world that many first-time readers do not associate with Spain. |
| 04 | Ribeira Sacra / Sil Canyon | ATLAS VIEW | APPROVED / KEEP | River gorge + steep vineyards show how people have reshaped difficult terrain for agriculture. |
| 05 | Las Médulas / Mirador de Orellán | ATLAS VIEW + DISCOVERY | APPROVED | Red clay peaks and chestnut forest reveal a landscape physically transformed by Roman hydraulic gold mining. |
| 06 | Consuegra / Cerro Calderico | ANCHOR + ATLAS VIEW | APPROVED / KEEP | The broad La Mancha plateau, windmills and wind-shaped cultural landscape create a recognisable inland Spain. |
| 07 | Ronda / Puente Nuevo + Tajo | ANCHOR + ATLAS VIEW | APPROVED | The city is split by a deep gorge and reconnected by Puente Nuevo: terrain and urban form are inseparable. |
| 08 | Teide / Roques de García | DISCOVERY | APPROVED / KEEP | Makes clear that Spain also includes a high volcanic Atlantic-island world far beyond the peninsula. |

### Removed from the 8

- Monfragüe National Park
  - Valuable for ecology and inland Mediterranean landscape.
  - Removed because its "I want to see this" pull is weaker than Las Médulas within an eight-scene limit.
- Cabo de Gata / Mónsul
  - Useful for explaining south-eastern aridity and volcanic coast.
  - Removed because its explanatory value is stronger than its destination pull.
- These approved assets remain archived / unused until a later editorial use is decided. Do not delete them during the pilot.

## 4. Scene-copy rule

Each scene copy must contain:

1. What the reader can actually see.
2. Why that view changes or deepens the reader's understanding of Spain.

Optional only when natural:
- light
- sound
- smell
- temperature
- season
- time of day
- people in motion

Do not force sensory writing into all eight scenes.

### Draft direction — Las Médulas

Red clay ridges rise between chestnut woods. The strange profile looks geological at first, but much of it is the trace of Roman gold mining that used hydraulic force to break apart the mountain. The scene shows how an ancient industry can remain legible in the land itself.

### Draft direction — Ronda

White buildings stand on both edges of a gorge more than 100 metres deep, joined by the stone mass of Puente Nuevo. Ronda is not simply a town with a famous bridge: its street structure and expansion make sense only when the gorge is seen as part of the city.

## 5. TASTE OF SPAIN

Purpose: food should reveal geography, agriculture and life — not become a restaurant guide.

### 01 Paella Valenciana

- Region: Valencia
- Core idea: rice landscape -> regional cooking.
- Sensory direction: rice absorbs the stock and ingredients; the shallow pan leaves a drier, more concentrated texture than soupy rice dishes.
- ATLAS connection: rice cultivation around Valencia, including the Albufera landscape, connects wetland agriculture to one of Spain's best-known dishes.
- Do not present seafood paella as the single canonical Valencian form.

### 02 Jamón Ibérico de bellota

- Region: mainly western / south-western dehesa landscapes
- Core idea: oak pasture -> animal husbandry -> flavour.
- Sensory direction: thin slices soften at room temperature, with salt, cured-meat depth and nut-like richness.
- ATLAS connection: the dehesa is not just scenery; grazing and acorn feeding are part of how the product is made.

No restaurant lists, ordering phrases or price guidance in this block.

## 6. Seasons — visualisation rule

Replace "best season" scoring with a 12-month climate-rhythm view.

Rows:
- North / Atlantic
- Central plateau
- Mediterranean coast / Andalusia
- Canary Islands

The visual should communicate broad seasonal change, not a universal recommendation score.

Editorial states may include:
- cool / wet
- mild
- hot / dry
- stable-mild
- mountain snow note where relevant

Keep the existing narrative season text only if it adds information not already obvious from the visual.

## 7. TRAVEL SCALE

Purpose: help the reader imagine the size of a Spain trip without giving a model itinerary.

- 3–4 days: one city or one compact region.
- 7–10 days: connect two or three contrasting regions.
- 2 weeks+: slow down, add rural / mountain areas, or combine mainland Spain with an island region.

Do NOT add:
- sample budgets
- hotel tiers
- daily itineraries
- rail timetables
- airport transfer instructions

## 8. JOURNEY LENS

Current state: HIDDEN FOR SPAIN.

As of 2026-09-02, no Spain story was found in the current JOURNEY LENS story index.

Rules:
- Never fabricate a LENS story or link to a generic page as if a Spain story exists.
- Show the country-level LENS block only when at least one matching Spain story exists.
- ATLAS role: discover / understand the country.
- LENS role: see an actual first-person photographic journey.

## 9. Current image production state

- H — Granada / Alhambra — APPROVED
- S01 — Barcelona / Turó de la Rovira — APPROVED
- S02 — San Sebastián / La Concha — APPROVED
- S03 — Picos de Europa / Picu Urriellu — APPROVED
- S04 — Ribeira Sacra / Sil Canyon — APPROVED
- S05 — Las Médulas / Mirador de Orellán — APPROVED
- S06 — Consuegra / Cerro Calderico — APPROVED
- S07 — Ronda / Puente Nuevo + Tajo — APPROVED
- S08 — Teide / Roques de García — APPROVED

VISUAL COMPLETE GATE: PASSED. Hero + S01–S08 are approved.

## 10. Implementation gate

Do not modify production Country JSON / shared template for the V3 layout until S05 and S07 are approved.

After Visual Complete:
1. Update Spain scenes and map markers from the same JSON.
2. Add optional shared components for Taste, season visualisation and Travel Scale.
3. Components must hide cleanly for countries with no corresponding data.
4. Do not add Spain-only CSS.
5. Keep JOURNEY LENS hidden for Spain until real Spain content exists.
6. QA Desktop / Tablet / Mobile / accessibility / map markers / asset paths / image decode.
