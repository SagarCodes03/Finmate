---
name: FinMate Fintech AI System
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#444651'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#747682'
  outline-variant: '#c4c6d2'
  surface-tint: '#3f5ba3'
  primary: '#001645'
  on-primary: '#ffffff'
  primary-container: '#002970'
  on-primary-container: '#7893df'
  inverse-primary: '#b3c5ff'
  secondary: '#006686'
  on-secondary: '#ffffff'
  secondary-container: '#2bc6ff'
  on-secondary-container: '#004f69'
  tertiary: '#001938'
  on-tertiary: '#ffffff'
  tertiary-container: '#002e5d'
  on-tertiary-container: '#6a97dc'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae1ff'
  primary-fixed-dim: '#b3c5ff'
  on-primary-fixed: '#001849'
  on-primary-fixed-variant: '#25438a'
  secondary-fixed: '#c0e8ff'
  secondary-fixed-dim: '#71d2ff'
  on-secondary-fixed: '#001e2b'
  on-secondary-fixed-variant: '#004d66'
  tertiary-fixed: '#d5e3ff'
  tertiary-fixed-dim: '#a7c8ff'
  on-tertiary-fixed: '#001b3c'
  on-tertiary-fixed-variant: '#074786'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 30px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
  title-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.03em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.25rem
  margin: 1.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.25rem
---

## Brand & Style

The design system embodies an authoritative yet accessible financial companion tailored for modern Indian consumers and businesses. It establishes a high-trust digital posture: balanced, compliant, sharp, and technologically proactive. The interaction paradigm blends the familiarity of leading Indian payments platforms with the intelligent restraint of an AI-driven financial advisory console.

### Visual Style
- **Corporate / Modern High-Trust Fintech**: Dominated by high-key, pristine white backdrops, soft slate surfaces, and structural crispness.
- **Atmospheric Palette**: Anchored in deep institutional indigo and charged with vibrant cyan accents to signal real-time AI processing, eligibility checks, and transaction automation.
- **Emotional Intent**: Certainty, regulatory composure, technological velocity, and zero ambiguity regarding financial decisions and Rupee movements.

## Colors

The palette is engineered around institutional security, high-contrast legibility, and rapid comprehension of complex financial telemetry.

### Core Roles
- **Primary (`#002970`)**: The authoritative base used for primary headers, navigational structures, high-value commitment buttons, and grounding anchors.
- **Secondary (`#00BAF2`)**: The digital intelligence accelerator. Used for AI telemetry highlights, active state pips, inline conversational accents, and progress indicators.
- **Tertiary (`#0F4A8A`)**: Mid-tone banking blue for sub-navigation, contextual cards, secondary actions, and metric callouts.
- **Neutral (`#64748B`)**: Precision slate used for secondary labels, regulatory disclosures, microcopy, and subtle boundary strokes.

### Semantic Triage Roles
- **Emerald (`#059669` / Background `#ECFDF5`)**: Pre-approved status, positive yields, completed UPI handshakes, and statutory eligibility.
- **Amber (`#D97706` / Background `#FFFBEB`)**: Manual risk intervention, pending documentation review, and transaction verification timeouts.
- **Indigo/Blue (`#1D4ED8` / Background `#EFF6FF`)**: Goal recovery vectors, SIP portfolio adjustments, and systemic rebalancing alerts.
- **Slate Neutral (`#475569` / Background `#F1F5F9`)**: Omitted KYC inputs, unlinked bank accounts, and dormant records.

## Typography

The type system blends the energetic geometry of **Plus Jakarta Sans** for prominent headers with the structural, tabular-ready neutrality of **Inter** for core banking experiences, transactional entries, and numerical summaries.

### Numerical and Currency Directives
- Tabular figures (`font-variant-numeric: tabular-nums`) must be enabled on all ledger views, account cards, balance rows, and currency comparisons.
- The Indian Rupee symbol (`₹`) is rendered alongside figures without additional space (e.g., `₹2,45,000.00`).
- Indian numbering grouping rules apply across all levels: two-digit grouping following the initial three digits (Lakhs and Crores: `₹12,50,000` rather than `₹1,250,000`).

## Layout & Spacing

A unified 8pt spatial cadence maintains rigorous vertical and horizontal alignment across enterprise dashboards and quick-access consumer touchpoints.

### Responsive Breakpoints & Grids
- **Mobile (< 768px)**: 4-column fluid layout with `16px` outer margins and `12px` gutters. AI companion actions, prompt chips, and account cards stack vertically.
- **Tablet (768px - 1023px)**: 8-column layout with `24px` margins and `16px` gutters. Split layout surfaces financial telemetry beside the interactive assistant.
- **Desktop (≥ 1024px)**: 12-column grid capped at `1440px` maximum width. Standard layout allocates 8 columns for journey milestones, ledger states, and decision nodes, and 4 persistent columns for the proactive AI companion thread.

## Elevation & Depth

Visual depth is achieved through layered tonal surfaces and calibrated, cold-tinted ambient shadows.

### Surface Hierarchy
- **Base Canvas**: Soft cool slate tint (`#F8FAFC`) to minimize glare during extended operational usage.
- **Layer 01 (Structural Panels & Cards)**: Pristine white (`#FFFFFF`) with a subtle border stroke (`1px solid #E2E8F0`).
- **Layer 02 (Interactive Modules & Popovers)**: White elevated surfaces paired with ambient blue shadows (`0 8px 24px -4px rgba(0, 41, 112, 0.08)`).
- **Layer 03 (Modals & Critical Overlays)**: Elevated focus layers (`0 16px 36px -6px rgba(0, 41, 112, 0.16)`) coupled with a slate backdrop veil (`rgba(15, 23, 42, 0.45)` with `backdrop-filter: blur(4px)`).

## Shapes

The interface balances soft modern touchpoints with institutional precision.

- **Standard Cards, Panels, and Containers**: Set to `rounded-xl` (12px on desktop, 10px on compact screens) to evoke an approachable fintech feel without losing data density.
- **Inputs, Buttons, and Selectors**: Set to 8px corner radii (`rounded-md` / `rounded-lg`) ensuring crisp alignment with baseline grids.
- **Interactive Badges, Pill Filters, and Status Indicators**: Full pill treatment (`rounded-full`) to differentiate discrete metadata tags from interactive form modules.

## Components

### Buttons
- **Primary CTA**: Deep indigo background (`#002970`), white text, medium weight, 8px corner radius. Includes a subtle transition to an interactive gradient accent (`#0F4A8A`) on hover.
- **Secondary / AI Action**: Cyan-blue tinted surface (`#E0F7FE`), vibrant cyan stroke, deep indigo text (`#002970`). Used for AI-suggested auto-payments, calculations, or verification triggers.
- **Destructive**: Pale red base (`#FEF2F2`) with red text (`#DC2626`) and matching outline (`#FECACA`).

### Status Badges & Chips
Status indicators combine a subtle background, crisp border, high-contrast text, and a leading 6px colored pip:
- **Eligible / Verified**: Green background (`#ECFDF5`), green border (`#A7F3D0`), green text (`#065F46`).
- **Human Review**: Amber background (`#FFFBEB`), amber border (`#FDE68A`), amber text (`#92400E`).
- **Goal Recovery**: Indigo background (`#EFF6FF`), blue border (`#BFDBFE`), blue text (`#1E40AF`).
- **Missing Info**: Slate background (`#F1F5F9`), slate border (`#CBD5E1`), slate text (`#334155`).

### Input Fields & Controls
- Form controls use a crisp white canvas framed by a 1px border in `#CBD5E1`.
- Focused state applies an indigo highlight border (`#002970`) accompanied by a 3px soft cyan ambient halo (`rgba(0, 186, 242, 0.2)`).
- Input groups dedicated to financial entries feature a fixed `₹` prefix rendered in `#64748B` with automatic Indian comma formatting applied during typing.

### Financial Summary Cards
- White ground framed by 1px `#E2E8F0` border and a light ambient shadow.
- Metrics display the tabular-formatted Indian Rupee balance in deep indigo, with supporting trend indicators and AI insight notes docked at the bottom over an ultra-light slate divider.