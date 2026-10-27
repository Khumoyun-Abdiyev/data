# IDENEL Professional Seminar: Meta carousel (5 × 1080×1080)

Files:
- `export/idenel-seminar-0X-*.png` and `.jpg` are the final cards. Upload the JPGs to Meta and keep the PNGs as masters.
- `carousel.html` is the editable source. All copy, colours and positions are in this one file.
- `render.js` re-exports the cards after edits. Run `node render.js` (needs Playwright + Chromium).
- `assets/` holds the product cut-outs taken from the official IDENEL "Glassifier" routine image.

---

## Cards

| # | Text on the card (Uzbek Latin) | Visual concept | Meta headline (≤40) | Meta description |
|---|---|---|---|---|
| 1 | IDENEL · 01/05 · **KOSMETOLOG va DERMATOLOGLAR DIQQATIGA!** · IDENEL PROFESSIONAL SEMINAR · Nazariya, amaliyot va professional skincare texnologiyalari · TOSHKENT | Oversized black headline speaks to specialists first. Three real IDENEL products (CC cream, SPF serum, tube cream) stand on a pearl plinth. | Mutaxassislar uchun IDENEL seminari | Kosmetolog va dermatologlar uchun |
| 2 | IDENEL · 02/05 · SEMINAR MAVZUSI · **MIKROIGNALAR BILAN ISHLASH TEXNOLOGIYALARI** · Professional yondashuv va texnologiyalar bilan yaqindan tanishing. | The real IDENEL microneedle kit sits in a white gallery panel. An abstract skin-layer diagram adds a light scientific feel. There is no procedure photo, no blood and no claim about results. | Mikroignalar bilan ishlash | Nazariya va amaliyot |
| 3 | IDENEL · 03/05 · SEMINAR MAVZUSI · **UY PARVARISHI VOSITALARINI TO‘G‘RI TANLASH** · Terini parvarishlash bosqichlari va IDENEL mahsulotlari bilan tanishing. · 1 Tozalash · 2 Tonik · 3 Zardob · 4 Krem · 5 SPF | Five real products laid out as a numbered routine. The order and categories follow IDENEL's own routine chart. No product benefits are stated. | Uy parvarishini to‘g‘ri tanlash | IDENEL mahsulotlari bilan |
| 4 | IDENEL · 04/05 · SEMINAR FORMATI · **NAZARIYA va AMALIYOT — BIR SEMINARDA** · Kabinet sharoitidagi kosmetologik protseduralarning amaliy namoyishi. · NAZARIYA I · AMALIYOT II | Two editorial tiles in gold line art: a lecture tile and a treatment-room tile (couch, magnifier lamp, trolley). No real or invented person appears. | Nazariya va amaliyot birga | Amaliy namoyish bilan |
| 5 | IDENEL · 05/05 · RO‘YXATDAN O‘TING · **BILIMINGIZNI BOYITING. SERTIFIKATINGIZNI OLING.** · Seminar yakunida har bir ishtirokchiga sertifikat beriladi. · [HOZIROQ ARIZA QOLDIRING →] · TOSHKENT SHAHRI \| JOYLAR SONI CHEKLANGAN | A clearly illustrative certificate: wordmark, "SERTIFIKAT", blank lines and a plain gold seal. It has no name, number or accreditation. A full-width gold CTA bar sits below it. | Ariza qoldiring: sertifikat beriladi | Joylar soni cheklangan |

Suggested primary text (for the field above the carousel):
> Kosmetolog va dermatologlar uchun IDENEL professional seminari — Toshkentda. Mikroignalar texnologiyalari, uy parvarishi vositalarini tanlash va kabinet protseduralarining amaliy namoyishi. Har bir ishtirokchiga sertifikat. Batafsil ma’lumot olish uchun ariza qoldiring.

CTA button in Ads Manager: **Ro‘yxatdan o‘tish** (Sign up) or **Batafsil** (Learn more).

---

## Style guide

| Token | Value | Use |
|---|---|---|
| Pearl | `#F6F3EE` → `#ECE6DC` radial | Background |
| Ink | `#1F1E1C` | Headlines |
| Ink-2 | `#55514B` | Body copy |
| Champagne gold | `#A9844C` / light `#CDB287` | Accent words, hairlines, CTA |
| Hairline frame | gold at 28%, inset 36 px | Same on every card |

- **Type:** headlines use Montserrat ExtraBold in uppercase (50–86 px). Body copy uses Montserrat Medium at 27 px. Small labels use Montserrat SemiBold at 15–17 px with wide tracking. The wordmark and accent words use Cormorant Garamond (italic for "va").
- **Grid:** 80 px safe margin. The wordmark is top-left and the page count ("0X / 05") is top-right, in the same place on every card. A footer hairline closes the bottom.
- **Accent rule:** each headline has exactly one gold phrase.
- **Products:** only real IDENEL packaging, blended with multiply onto the pearl background, with soft contact shadows.
- **Do not use:** pink, glitter, flowers, before-and-after photos, people, or prices, dates or venues.

## Export settings
- 1080 × 1080 px, sRGB, 1:1.
- Upload JPG at quality 95 (about 150–300 KB). Keep the PNGs as lossless masters.
- In Ads Manager: Carousel format with "Show the best performing cards first" **off**, so the 1→5 story order is kept.

## QC checklist
- [x] Spelling: Uzbek Latin throughout, using the ‘ apostrophe as in the brief (to‘g‘ri, ro‘yxatdan o‘ting). If your brand standard uses the official ʻ (U+02BB), swap it in `carousel.html`.
- [x] No Russian text. The only English is the brand name and the brief's own "IDENEL PROFESSIONAL SEMINAR" and "skincare".
- [x] No date, time, venue, price, speaker, URL, phone or QR code.
- [x] No efficacy or medical claims, no fake accreditation, and the certificate is illustrative only.
- [x] All copy sits inside the 80 px safe margin, and the smallest text is 15 px (readable on mobile at feed size).
- [x] Logo position, frame, palette and type are the same on all 5 cards.
- [ ] **Confirm before launch:** "Joylar soni cheklangan" is only true if seats really are capped.
- [ ] **Confirm before launch:** the seminar really covers the IDENEL microneedle kit shown on card 2.
- [ ] **Swap before launch:** replace the typeset "IDENEL" wordmark with the official logo file (SVG/PNG).
- [ ] **Optional:** replace product cut-outs with high-resolution packshots from IDENEL. The current ones are upscaled from a social-media image.
