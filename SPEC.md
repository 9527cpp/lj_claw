# lj_claw UI Design Specification
Based on Claude Design System (MIT License)

## Overview
lj_claw is an AI chat agent with a warm, editorial feel. Anchored on a tinted cream canvas with warm coral CTAs and clean sans-serif body. The design should feel like a literary publication — warm, humanist, and premium.

## Color Palette

### Brand & Accent
- **Primary / Coral** `#cc785c` — signature warm coral, used for CTAs and active states
- **Primary Active** `#a9583e` — hover/press darker coral
- **Primary Disabled** `#e6dfd8` — desaturated cream for disabled states

### Surface
- **Canvas** `#faf9f5` — tinted warm cream, default page background
- **Surface Card** `#efe9de` — slightly darker cream, used for feature cards, session items
- **Surface Dark** `#181715` — dark navy for code blocks, chat bubbles (assistant)
- **Surface Dark Elevated** `#252320` — elevated dark cards
- **Hairline** `#e6dfd8` — 1px border color

### Text
- **Ink** `#141413` — headlines, primary text (warm dark, not pure black)
- **Body** `#3d3d3a` — default running text
- **Muted** `#6c6a64` — sub-headings, secondary text
- **On Primary** `#ffffff` — text on coral buttons
- **On Dark** `#faf9f5` — cream text on dark surfaces

### Semantic
- **Success** `#5db872`
- **Warning** `#d4a017`
- **Error** `#c64545`

## Typography
- **Display**: Inter (or -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif), 400 weight
- **Body**: Inter, 14-16px, 400 weight
- **Code**: JetBrains Mono or ui-monospace, 14px

### Scale
| Token | Size | Weight | Use |
|-------|---|-------|-----|
| display-xl | 48px | 400 | Page titles |
| display-lg | 36px | 400 | Section heads |
| title-lg | 22px | 500 | Card titles |
| title-md | 18px | 500 | Sub-headings |
| title-sm | 16px | 500 | List labels |
| body-md | 16px | 400 | Body text |
| body-sm | 14px | 400 | Secondary text, captions |
| button | 14px | 500 | Button labels |
| nav-link | 14px | 500 | Nav items |

## Spacing
Base unit: 4px
- xs: 8px · sm: 12px · md: 16px · lg: 24px · xl: 32px · xxl: 48px

## Border Radius
- xs: 4px · sm: 6px · md: 8px · lg: 12px · xl: 16px · pill: 9999px

## Layout

### Desktop (≥769px)
- App sidebar: 200px fixed left, cream canvas background
- Sessions sidebar: 280px fixed left (inside main content area)
- Main content: fluid, max-width ~800px centered
- Chat input: max-width 800px centered at bottom

### Mobile (≤768px)
- App sidebar: hidden by default, slides in from left (-200px)
- Sessions sidebar: hidden by default, slides in from left (-280px)
- Mobile menu button: fixed top-left
- Mobile sessions button: fixed top-left

## Components

### App Sidebar
- Background: `{colors.canvas}` `#faf9f5`
- Text color: `{colors.ink}` `#141413`
- Active link: coral `#cc785c` text
- Border right: 1px `{colors.hairline}` `#e6dfd8`
- z-index: 300 (above sessions sidebar)

### Sessions Sidebar
- Background: `{colors.canvas}` `#faf9f5`
- Session item hover: `{colors.surface-card}` `#efe9de`
- Active session: left border 3px coral `#cc785c`
- z-index desktop: 80 · mobile: 170

### Chat Input Area
- Background: `{colors.canvas}` with top border
- Input field: rounded 24px, hairline border, 40px height
- Send button: coral `#cc785c` background, white text, rounded pill
- Stop button: gray circle, red on hover

### Chat Messages
- User message bubble: coral `#cc785c` background, white text, rounded 16px, right-aligned
- Assistant message: `{colors.canvas}` background, ink text, rounded 16px, left-aligned
- Thinking indicator: `{colors.muted}` italic text

### Buttons
- Primary: coral background `#cc785c`, white text, rounded 8px, height 40px
- Secondary: cream canvas background, ink text, hairline border
- Icon circular: 36px circle, canvas background, hairline border
- Disabled: `#e6dfd8` background, muted text

### Search Toggle
- Inactive: white background, muted text, hairline border
- Active: `#e3f2fd` background, `#1976D2` text, blue border
- Icon: globe or search SVG

## Elevation Philosophy
- Color-block first, shadow rare
- Most depth comes from cream-vs-dark surface contrast
- No heavy drop shadows — only subtle hairline borders

## Breakpoints
- Mobile: < 768px
- Desktop: ≥ 769px
- Touch targets: minimum 40×40px
