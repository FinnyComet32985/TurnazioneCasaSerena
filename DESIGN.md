# Design System Document: The Clinical Architect

## 1. Overview & Creative North Star
**Creative North Star: "The Ethereal Monolith"**

In the high-stakes environment of healthcare management, "clean" is a prerequisite, but "intentionality" is the signature. This design system moves beyond the generic "SaaS dashboard" look to create a **Clinical Architect** aesthetic. It blends the structural rigidity of a professional ERP with an editorial, high-end lightness.

We break the "template" look by utilizing **intentional asymmetry**—where the heavy, high-contrast dark sidebar acts as a grounding anchor for a fluid, airy, and light-filled workspace. By rejecting traditional 1px grid lines in favor of **Tonal Layering**, we create a UI that feels like stacked sheets of architectural vellum: precise, professional, and sophisticated.

---

## 2. Colors: Tonal Depth & The "No-Line" Rule
The palette is rooted in medical reliability (`primary: #004d99`) but elevated through a sophisticated grayscale that uses temperature to define function.

### The Color Logic
*   **The Foundation:** Use `surface` (#f8fafb) for the broad canvas. It is slightly off-white to reduce eye strain for users in their 50s.
*   **The Sidebar (High Contrast):** Utilize `inverse_surface` (#2e3132) for the primary navigation. This creates a "Monolithic" anchor that focuses the user's eye on the workspace.
*   **The "No-Line" Rule:** Absolute prohibition of `1px solid #CCC` style borders for layout sectioning. Separation of concerns must be achieved through background shifts. For example, a "Search & Filter" bar should be `surface_container_low` (#f2f4f5) sitting atop a `surface` background.
*   **Signature Textures:** For primary Action Buttons or high-level status cards, apply a subtle linear gradient from `primary` (#004d99) to `primary_container` (#1565c0) at a 135-degree angle. This adds "soul" and a tactile, premium depth that flat hex codes lack.

---

## 3. Typography: The Editorial Hierarchy
To support users in their 50s, we prioritize **optical legibility** over high-density information. We use *Public Sans*—a typeface designed for government and healthcare—ensuring a neutral but authoritative voice.

*   **Display & Headline:** Use `headline-lg` (2rem) for page titles. Bold weights should be reserved for `title-lg` (1.375rem) to ensure clear section scanning.
*   **The Body Standard:** Our "Default" is `body-lg` (1rem). Never drop below `body-sm` (0.75rem) for any legal or clinical data.
*   **Rhythm:** Maintain a generous line-height (1.6x) for body text. This prevents "text-bleeding" when reading long patient histories or ERP logs.

---

## 4. Elevation & Depth: Tonal Layering
We move away from the "shadow-heavy" look of the 2010s toward **Physical Stacking**.

*   **The Layering Principle:** 
    *   **Base:** `surface` (#f8fafb)
    *   **Sectioning:** `surface_container` (#eceeef)
    *   **Interactable Cards:** `surface_container_lowest` (#ffffff)
    *   This stacking creates a natural lift. A white card on a light gray background is the "Clinical Architect" way of defining a container.
*   **Ambient Shadows:** If a modal or floating menu is required, use a shadow with a 20px–40px blur, 4% opacity, using the `on_surface` color tinted with a hint of `primary`. It should feel like a soft glow, not a dark smudge.
*   **The Ghost Border:** For form inputs where accessibility requires a perimeter, use `outline_variant` at 20% opacity. It should be felt, not seen.

---

## 5. Components: Robust Utility

### Buttons (The Primary Anchors)
*   **Primary:** High-contrast `primary` with `on_primary` text. Radius: `md` (0.375rem). Use the signature gradient mentioned in Section 2.
*   **Secondary:** `surface_container_high` background with `on_surface_variant` text. This avoids visual clutter when multiple actions are present.

### Form Inputs (The Data Entry Standard)
*   **Text Fields:** Use a `surface_container_lowest` (white) background. 
*   **Interaction:** On focus, the border transitions from a "Ghost Border" to a 2px `primary` stroke. 
*   **Labels:** Always use `title-sm` (1rem) for labels—never small captions—to ensure clinicians can identify fields at a glance.

### Cards & Lists (The Data Grid)
*   **Forbid Dividers:** Do not use horizontal lines between list items. Use `spacing-4` (1rem) of vertical whitespace and a subtle hover state change to `surface_container_low`.
*   **The High-Contrast Sidebar:** Navigation items in the sidebar use `inverse_on_surface` text. The "Active" state should be a `primary_container` left-accent bar (4px) with a soft `surface_tint` glow.

### Specialized Component: The Patient Pulse-Card
A custom component for this system. A `surface_container_lowest` card with a `primary_fixed` (light blue) top-border (4px). It uses `headline-sm` for the patient name, providing immediate visual hierarchy in a high-density management tool.

---

## 6. Do’s and Don’ts

### Do:
*   **Use Asymmetric Padding:** Allow for more white space on the right side of the screen than the left to give the eye a place to "rest" during complex data entry.
*   **Stack Surfaces:** Place `surface_container_highest` elements inside `surface` containers to denote "Toolboxes" or "Utility Panels."
*   **Prioritize Public Sans:** Ensure all clinical data uses the `body-lg` token for maximum readability.

### Don’t:
*   **Don't use 1px black borders:** They create "visual noise" that fatigues healthcare workers during long shifts. Use tonal shifts instead.
*   **Don't use pure white backgrounds for the entire screen:** It causes glare. Use `surface` (#f8fafb) as the base.
*   **Don't crowd the Sidebar:** Keep navigation items sparse. Use `spacing-6` between nav elements to prevent "fat-finger" errors on touch-enabled desktop monitors.

---

## 7. Color Reference

### Primary Tokens
*   **primary:** `#004d99`
*   **primary_container:** `#1565c0`
*   **on_primary:** `#ffffff`
*   **on_primary_container:** `#dae5ff`
*   **primary_fixed:** `#d6e3ff`

### Secondary & Tertiary
*   **secondary:** `#4a5f83`
*   **secondary_container:** `#c0d5ff`
*   **tertiary:** `#813900`
*   **tertiary_container:** `#a64c00`

### Surface Tokens
*   **surface:** `#f8fafb`
*   **on_surface:** `#191c1d`
*   **surface_container_lowest:** `#ffffff`
*   **surface_container_low:** `#f2f4f5`
*   **surface_container:** `#eceeef`
*   **surface_container_high:** `#e6e8e9`
*   **surface_container_highest:** `#e1e3e4`
*   **surface_dim:** `#d8dadb`
*   **surface_bright:** `#f8fafb`
*   **inverse_surface:** `#2e3132`
*   **inverse_on_surface:** `#eff1f2`

### Form & Borders
*   **outline:** `#727783`
*   **outline_variant:** `#c2c6d4`
*   **error:** `#ba1a1a`
*   **error_container:** `#ffdad6`
