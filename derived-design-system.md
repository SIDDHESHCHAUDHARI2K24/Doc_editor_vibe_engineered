# Derived Design System

**Purpose**: Concrete visual specs for non-editor UI (dashboard, login, share dialog, modals, lists, toasts) derived from the WYSIWYG kit's editor frames. Coding agents implement against this document deterministically — they do not need to query Figma at code time for non-editor surfaces.

**Source**: Two reference frames from the [WYSIWYG Text Editor UI Kit](https://www.figma.com/design/Of62CmYJ3KkXoorrp5jIaU/WYSIWYG-Text-Editor-UI-Kit--Community-): the in-context editor render (with full app chrome, document body, toolbar) and the three-variant toolbar specimen.

**Scope of this document**:
- Color tokens
- Type ramp
- Spacing scale
- Component patterns: buttons, dropdowns, dialogs, list rows, toolbar
- Tailwind config inputs

**Out of scope**: motion/animation specs, dark mode (deferred — kit shows light mode only), high-fidelity icons (use `lucide-react` consistently).

---

## Color Tokens

Hex values are inferred from the editor render. They are calibrated, not exact — a designer may tweak by ±5% lightness without breaking the system. Coding agents use these as authoritative until/unless someone updates this doc.

### Brand & accent

| Token | Hex | Usage |
|---|---|---|
| `--color-brand` | `#5B5BD6` | The "✦ TextEditor" logo mark; primary CTA buttons (e.g., "Preview" pill in the kit, our "Sign in" button, "Create document" button) |
| `--color-brand-hover` | `#4848B8` | Hover state for brand-colored interactive elements |
| `--color-brand-active` | `#3A3A99` | Pressed state |
| `--color-accent` | `#2D5BFF` | Secondary accent — text color swatch in toolbar, active-checkbox fill, focus ring color |
| `--color-accent-hover` | `#1F47D6` | Hover state for accent elements |

### Neutrals (light mode)

| Token | Hex | Usage |
|---|---|---|
| `--color-canvas` | `#F1F5F9` | Outer page background (the cool-gray "desk" behind the white document) |
| `--color-surface` | `#FFFFFF` | Card / document / dialog / toolbar background |
| `--color-surface-raised` | `#FFFFFF` + shadow | Dropdown menus, popovers (background same as surface; visual lift via shadow) |
| `--color-border-subtle` | `#E2E8F0` | Default borders on inputs, dividers between toolbar rows, table separators |
| `--color-border-strong` | `#CBD5E1` | Hovered/focused input borders, prominent dividers |
| `--color-text-primary` | `#0F172A` | Body text, headings |
| `--color-text-secondary` | `#475569` | Subtitle text, list metadata, breadcrumbs |
| `--color-text-muted` | `#64748B` | "0 words" counter, placeholder text, disabled labels |
| `--color-text-inverse` | `#FFFFFF` | Text on brand/accent backgrounds (e.g., "Preview" button label) |
| `--color-bg-hover` | `#F8FAFC` | Row hover, button hover (subtle) |
| `--color-bg-selected` | `#EEF2FF` | Selected list row, active dropdown item |

### Semantic

| Token | Hex | Usage |
|---|---|---|
| `--color-success` | `#10B981` | Toast success, "Connected" indicators |
| `--color-warning` | `#F59E0B` | Toast warning |
| `--color-danger` | `#EF4444` | Toast error, destructive button (Delete confirm), validation error message |
| `--color-danger-hover` | `#DC2626` | Hover state for destructive elements |

### Focus ring

| Token | Value | Usage |
|---|---|---|
| `--ring-focus` | `0 0 0 3px rgba(45, 91, 255, 0.35)` | Outline on focused inputs, buttons, list items |

---

## Type Ramp

Inferred from the editor body and toolbar labels. Font family is `Inter` (chosen as a sane default given the kit uses a generic sans-serif; coding agents load Inter from Google Fonts).

| Token | Family | Size | Line-height | Weight | Letter-spacing | Usage |
|---|---|---|---|---|---|---|
| `--font-sans` | `'Inter', system-ui, sans-serif` | — | — | — | — | All text by default |
| `--font-mono` | `'JetBrains Mono', ui-monospace, monospace` | — | — | — | — | Reserved for future code blocks (out of S3 scope) |
| `--text-h1` | sans | `36px` | `1.2` | `700` | `-0.02em` | Document title (in the editor body) |
| `--text-h2` | sans | `24px` | `1.3` | `600` | `-0.01em` | Editor H2, dialog titles, dashboard section heads |
| `--text-h3` | sans | `20px` | `1.4` | `600` | `0` | Editor H3, dialog subtitles |
| `--text-body` | sans | `16px` | `1.6` | `400` | `0` | Body paragraphs, doc list item titles, form labels' adjacent inputs |
| `--text-body-medium` | sans | `16px` | `1.6` | `500` | `0` | Doc list item titles (slightly stronger), button labels in non-CTA buttons |
| `--text-body-strong` | sans | `16px` | `1.6` | `600` | `0` | Button labels in CTA buttons |
| `--text-small` | sans | `14px` | `1.5` | `400` | `0` | Subtitle below title, form labels, toolbar dropdown labels (`Paragraph text`), list-row metadata (e.g., "2h ago") |
| `--text-caption` | sans | `12px` | `1.4` | `400` | `0.01em` | "0 words" counter, helper text under inputs |

**Editor-body specifics** (these don't apply elsewhere; Quill controls them in the editor):
- Default paragraph: `--text-body`
- H1 in editor body: `--text-h1`
- H2 in editor body: `--text-h2`
- H3 in editor body: `--text-h3`
- Bulleted/numbered list items: `--text-body`

---

## Spacing Scale

Standard 4px base. Tailwind's default scale fits — we don't need a custom one.

| Tailwind | Pixels | Common use |
|---|---|---|
| `space-1` | 4px | Icon-button inner padding, tight chip padding |
| `space-2` | 8px | Inline gaps between toolbar groups |
| `space-3` | 12px | Form field internal padding (vertical), default button padding |
| `space-4` | 16px | Section vertical rhythm, dialog content padding |
| `space-6` | 24px | Section gaps in larger layouts (sidebar to main column) |
| `space-8` | 32px | Page padding on dashboards |

**Toolbar-specific**:
- Toolbar height: `48px` per row (kit shows two rows for ~96px total)
- Button gap inside toolbar group: `4px`
- Group separator: vertical 1px line at `--color-border-subtle`, full toolbar height with `8px` margin on each side

---

## Border Radius

| Token | Value | Usage |
|---|---|---|
| `--radius-sm` | `4px` | Inline elements (chips, small buttons, toolbar buttons) |
| `--radius-md` | `8px` | Cards, inputs, dropdowns, dialogs, list rows |
| `--radius-lg` | `12px` | Large surfaces (the "document on desk" canvas card) |
| `--radius-pill` | `9999px` | The "Preview" pill button shape |

The kit's "Preview" CTA is pill-shaped. Apply pill radius to **primary CTAs** in our app (Sign in, Create document, Save share); use `--radius-md` for secondary/utility buttons.

---

## Shadow

| Token | Value | Usage |
|---|---|---|
| `--shadow-sm` | `0 1px 2px 0 rgba(15, 23, 42, 0.05)` | List row hover lift |
| `--shadow-md` | `0 4px 6px -1px rgba(15, 23, 42, 0.10), 0 2px 4px -2px rgba(15, 23, 42, 0.06)` | Dropdown menus, popovers |
| `--shadow-lg` | `0 10px 15px -3px rgba(15, 23, 42, 0.10), 0 4px 6px -4px rgba(15, 23, 42, 0.05)` | Dialogs / modals |

---

## Component Patterns

These specs are authoritative. When a stage plan says "use the standard Button primitive", it means this section.

### Button

Three variants. All have `font-medium` and `transition-colors`.

**Primary CTA (pill-shaped, brand)**
- Background: `--color-brand`; hover `--color-brand-hover`; active `--color-brand-active`
- Text: `--color-text-inverse`, `--text-body-strong`
- Padding: `10px 20px` (vertical / horizontal)
- Radius: `--radius-pill`
- Disabled: 50% opacity + cursor-not-allowed
- Focus: `--ring-focus`
- Tailwind sketch: `bg-[var(--color-brand)] hover:bg-[var(--color-brand-hover)] text-white font-semibold px-5 py-2.5 rounded-full`

**Secondary (outlined)**
- Background: transparent; hover `--color-bg-hover`
- Border: 1px `--color-border-strong`
- Text: `--color-text-primary`, `--text-body-medium`
- Padding: `8px 16px`
- Radius: `--radius-md`

**Destructive**
- Background: `--color-danger`; hover `--color-danger-hover`
- Text: `--color-text-inverse`, `--text-body-strong`
- Padding: `8px 16px`
- Radius: `--radius-md`

**Icon-only button (toolbar)**
- 32px × 32px square
- Background: transparent; hover `--color-bg-hover`; pressed `--color-bg-selected`
- Active-format state (e.g., bold-on): `--color-bg-selected` background + `--color-accent` icon color
- Icon size: 18px from `lucide-react`
- Radius: `--radius-sm`

### Input (text)

- Height: `40px`
- Padding: `8px 12px` horizontal
- Background: `--color-surface`
- Border: 1px `--color-border-subtle`; hover `--color-border-strong`; focus `--color-accent` + `--ring-focus`
- Text: `--text-body`, `--color-text-primary`
- Placeholder: `--color-text-muted`
- Radius: `--radius-md`
- Disabled: 50% opacity, no hover

### Dropdown (toolbar style)

Used in the editor toolbar (Style/Heading dropdown). Pattern:
- Trigger: looks like a label-with-caret button. Padding `4px 8px`. Caret icon `chevron-down` from lucide, 16px.
- Menu: `--color-surface-raised`, `--shadow-md`, `--radius-md`, padding `4px 0`, min-width matches trigger.
- Menu item: `12px 16px` padding, hover `--color-bg-hover`, active `--color-bg-selected` + `--color-accent` text.
- Item with format preview: render the option in the format it represents (e.g., "Heading 1" rendered as bold large text).

### Dialog / Modal

- Width: `480px` default; `560px` for wider forms (share dialog)
- Background: `--color-surface`, `--shadow-lg`, `--radius-md`
- Backdrop: `rgba(15, 23, 42, 0.4)` + `backdrop-blur-sm`
- Padding: `24px`
- Header: `--text-h2`, `--color-text-primary`, padding-bottom `16px`, border-bottom 1px `--color-border-subtle`
- Body: `--text-body`, `--color-text-primary`, padding-y `16px`
- Footer: right-aligned button row, gap `8px`, padding-top `16px`, border-top 1px `--color-border-subtle`
- Close: `X` icon button at top-right, `--color-text-muted`, 32px square
- Animation: fade-in backdrop + scale-from-0.95 dialog, 150ms ease-out

### List Row (dashboard, share-with-list, etc.)

- Height: `64px`
- Background: `--color-surface`; hover `--color-bg-hover`; selected `--color-bg-selected`
- Border-bottom: 1px `--color-border-subtle` (last child no border)
- Padding: `12px 16px`
- Layout (left-to-right, items separated by `gap-3`):
  1. Icon (24×24, `--color-text-secondary`)
  2. Title (`--text-body-medium`, `--color-text-primary`, truncate with ellipsis)
  3. Spacer (`flex-1`)
  4. Metadata (`--text-small`, `--color-text-secondary`, e.g., "2h ago")
  5. Actions (icon buttons; visible on row hover only on desktop)
- Title row clickable; clicking navigates. Action buttons stop propagation.

### Toast

- Width: `360px` max
- Position: bottom-right of viewport, `24px` from edges, stacked vertically with `8px` gap
- Background: `--color-surface`, `--shadow-md`, `--radius-md`
- Padding: `12px 16px`
- Layout: status icon (24px) + message (`--text-body`) + close button (16px X)
- Status icon color: `--color-success` / `--color-danger` / `--color-warning` based on type
- Auto-dismiss: 5 seconds; pause on hover
- Animation: slide-from-right 200ms ease-out

### Tab (dashboard "Owned by me" / "Shared with me")

- Container: row, `gap-1`, border-bottom 1px `--color-border-subtle`
- Tab item:
  - Padding: `10px 16px`
  - Text: `--text-body-medium`, `--color-text-secondary` default, `--color-text-primary` when active
  - Active indicator: `2px` solid bottom border, `--color-brand`, sits on top of the container's border
  - Hover: `--color-text-primary` text
- Switching: instant (no animation); ARIA `role="tablist"` and `role="tab"` correctly applied

### Toolbar (editor)

The detailed editor-toolbar spec lives in **Stage 3's plan**, since it's editor-specific. This entry establishes the **visual system tokens** the toolbar uses:

- Toolbar container: `--color-surface`, border-bottom 1px `--color-border-subtle`, height per row `48px`
- Toolbar uses **icon-only buttons** (see Button > Icon-only above) and **dropdowns** (see Dropdown above)
- Toolbar group separators: vertical 1px line, `--color-border-subtle`, height `24px`, margin-left/right `8px`
- Position: sticky top of editor scroll container (so it stays visible during long-document scroll)

---

## Tailwind Config Inputs

Coding agents drop these into `tailwind.config.ts` `theme.extend` to wire the tokens. CSS variables defined in `src/index.css` `:root` so we can flip them later for dark mode without touching Tailwind config.

```typescript
// tailwind.config.ts (extract — full file in frontend/)
export default {
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: 'var(--color-brand)',
          hover: 'var(--color-brand-hover)',
          active: 'var(--color-brand-active)',
        },
        accent: {
          DEFAULT: 'var(--color-accent)',
          hover: 'var(--color-accent-hover)',
        },
        canvas: 'var(--color-canvas)',
        surface: {
          DEFAULT: 'var(--color-surface)',
          raised: 'var(--color-surface-raised)',
        },
        border: {
          subtle: 'var(--color-border-subtle)',
          strong: 'var(--color-border-strong)',
        },
        text: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          muted: 'var(--color-text-muted)',
          inverse: 'var(--color-text-inverse)',
        },
        bg: {
          hover: 'var(--color-bg-hover)',
          selected: 'var(--color-bg-selected)',
        },
        success: 'var(--color-success)',
        warning: 'var(--color-warning)',
        danger: {
          DEFAULT: 'var(--color-danger)',
          hover: 'var(--color-danger-hover)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        h1: ['36px', { lineHeight: '1.2', letterSpacing: '-0.02em', fontWeight: '700' }],
        h2: ['24px', { lineHeight: '1.3', letterSpacing: '-0.01em', fontWeight: '600' }],
        h3: ['20px', { lineHeight: '1.4', fontWeight: '600' }],
        body: ['16px', { lineHeight: '1.6' }],
        small: ['14px', { lineHeight: '1.5' }],
        caption: ['12px', { lineHeight: '1.4', letterSpacing: '0.01em' }],
      },
      borderRadius: {
        pill: '9999px',
      },
      boxShadow: {
        // sm/md/lg map to the values in the Shadow section above
      },
    },
  },
};
```

```css
/* src/index.css (extract) */
:root {
  --color-brand: #5B5BD6;
  --color-brand-hover: #4848B8;
  --color-brand-active: #3A3A99;
  --color-accent: #2D5BFF;
  --color-accent-hover: #1F47D6;
  --color-canvas: #F1F5F9;
  --color-surface: #FFFFFF;
  --color-border-subtle: #E2E8F0;
  --color-border-strong: #CBD5E1;
  --color-text-primary: #0F172A;
  --color-text-secondary: #475569;
  --color-text-muted: #64748B;
  --color-text-inverse: #FFFFFF;
  --color-bg-hover: #F8FAFC;
  --color-bg-selected: #EEF2FF;
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-danger: #EF4444;
  --color-danger-hover: #DC2626;
}
```

---

## Iconography

Use `lucide-react` consistently across the app. Standard icon size: `18px` (toolbar), `20px` (dialog/list), `16px` (caret/inline).

**Mapping for our app's icons** (when an action needs an icon):

| Action | Lucide icon |
|---|---|
| Bold | `Bold` |
| Italic | `Italic` |
| Underline | `Underline` |
| Strikethrough | `Strikethrough` |
| Heading dropdown | `Type` (or `Heading`) |
| Bulleted list | `List` |
| Numbered list | `ListOrdered` |
| Link insert | `Link` (or `Link2`) |
| Clear formatting | `RemoveFormatting` |
| Undo | `Undo2` |
| Redo | `Redo2` |
| Document (in list) | `FileText` |
| Create new | `Plus` |
| More menu | `MoreHorizontal` |
| Delete | `Trash2` |
| Rename | `Pencil` |
| Share | `Share2` |
| Close dialog | `X` |
| Caret down | `ChevronDown` |
| Toast success | `CheckCircle2` |
| Toast warning | `AlertTriangle` |
| Toast error | `XCircle` |

---

## Out of Scope (Deferred)

These items intentionally do NOT have specs in this document. Adding them later is a deliberate design pass.

- Dark mode color tokens — kit shows light mode only; flag in README as "post-MVP"
- Animation / motion specs beyond the few baseline transitions noted above
- Print stylesheet / `@media print`
- Mobile breakpoint specs (locked to desktop-only per Stage 3 toolbar decision)
- High-fidelity custom illustrations / empty-state graphics
- Logo redesign (use the kit's "✦" star mark inline as `<svg>`)

When agents encounter a UI need not covered here, they should: (a) extend a closest-pattern entry, (b) add the new pattern to this document under a new section heading, (c) flag the addition in the PR description so a human can review the addition before it becomes canonical.

---

*End of derived-design-system.md*
