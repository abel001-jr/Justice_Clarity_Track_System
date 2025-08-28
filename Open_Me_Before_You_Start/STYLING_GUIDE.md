# Justice Clarity - Styling Guide

## Overview

This document outlines the styling architecture and design system for the Justice Clarity court case management system. The styling is built on a layered approach that ensures consistency across all dashboards while allowing for role-specific customization.

## CSS Architecture

### 1. Base Layer (`templates/base.html`)
- **Global CSS Variables**: Defines the core color palette and design tokens
- **Base Styles**: Common styles for layout, typography, and components
- **Responsive Design**: Mobile-first approach with breakpoints
- **Accessibility**: Focus states, screen reader support, and keyboard navigation

### 2. Main Styles (`static/css/styles.css`)
- **Global Utilities**: Additional utility classes and enhancements
- **Component Variations**: Extended button styles, form enhancements, alerts
- **Interactive Elements**: Hover states, transitions, and animations
- **Print Styles**: Optimized layouts for printing

### 3. Role-Specific Styles
- **Judge Dashboard** (`static/css/judge_dashboard.css`): Blue color scheme, legal-focused components
- **Clerk Dashboard** (`static/css/clerk_dashboard.css`): Green color scheme, administrative components
- **Prison Dashboard** (`static/css/prison_dashboard.css`): Red color scheme, security-focused components

## Design System

### Color Palette

#### Primary Colors (Role-Specific)
- **Judge**: `#1e3a8a` (Deep Blue) - Authority and professionalism
- **Clerk**: `#059669` (Emerald Green) - Efficiency and organization
- **Prison**: `#dc2626` (Crimson Red) - Security and alertness

#### Secondary Colors
- **Secondary**: `#64748b` (Slate Gray) - Neutral text and borders
- **Success**: `#059669` (Green) - Positive actions and completed states
- **Warning**: `#d97706` (Orange) - Caution and pending states
- **Danger**: `#dc2626` (Red) - Errors and urgent actions
- **Info**: `#0891b2` (Cyan) - Information and neutral states

### Typography

#### Font Stack
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
```

#### Font Weights
- **Regular**: 400 (default)
- **Medium**: 500 (buttons, labels)
- **Semibold**: 600 (headings, emphasis)
- **Bold**: 700 (main headings)

### Spacing System

#### Base Unit: 0.25rem (4px)
- **xs**: 0.25rem (4px)
- **sm**: 0.5rem (8px)
- **md**: 0.75rem (12px)
- **lg**: 1rem (16px)
- **xl**: 1.5rem (24px)
- **2xl**: 2rem (32px)
- **3xl**: 3rem (48px)

### Component Guidelines

#### Cards
- **Border Radius**: 0.75rem (12px)
- **Shadow**: `0 4px 6px rgba(0, 0, 0, 0.05)`
- **Hover Effect**: `translateY(-2px)` with enhanced shadow
- **Border Left**: 4px colored border for status indication

#### Buttons
- **Border Radius**: 0.5rem (8px)
- **Padding**: 0.75rem 1.5rem
- **Font Weight**: 500
- **Hover Effect**: `translateY(-1px)` with color transition

#### Forms
- **Border Radius**: 0.5rem (8px)
- **Focus State**: 3px outline with role-specific color
- **Border**: 1px solid `#d1d5db`
- **Padding**: 0.75rem

#### Tables
- **Header Background**: Role-specific gradient
- **Border Radius**: 0.75rem (12px)
- **Hover Effect**: Subtle background color change
- **Cell Padding**: 1rem

## Implementation Guidelines

### 1. Using Role-Specific Classes

#### Judge Dashboard
```html
<!-- Use judge-specific classes -->
<div class="stat-card judge-primary">...</div>
<div class="case-card urgent">...</div>
<button class="btn-judge-primary">...</button>
```

#### Clerk Dashboard
```html
<!-- Use clerk-specific classes -->
<div class="stat-card clerk-primary">...</div>
<div class="case-management-card new">...</div>
<button class="btn-clerk-primary">...</button>
```

#### Prison Dashboard
```html
<!-- Use prison-specific classes -->
<div class="stat-card prison-primary">...</div>
<div class="inmate-card warning">...</div>
<button class="btn-prison-primary">...</button>
```

### 2. Responsive Design

#### Mobile-First Approach
```css
/* Base styles (mobile) */
.component {
    padding: 1rem;
}

/* Tablet and up */
@media (min-width: 768px) {
    .component {
        padding: 1.5rem;
    }
}

/* Desktop and up */
@media (min-width: 1024px) {
    .component {
        padding: 2rem;
    }
}
```

### 3. Accessibility

#### Focus States
```css
.component:focus {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
}
```

#### Screen Reader Support
```html
<span class="sr-only">Hidden text for screen readers</span>
```

### 4. Animation Guidelines

#### Transitions
- **Duration**: 0.2s - 0.3s
- **Easing**: `ease` or `ease-out`
- **Properties**: `transform`, `opacity`, `box-shadow`

#### Hover Effects
```css
.component {
    transition: all 0.3s ease;
}

.component:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}
```

## Best Practices

### 1. CSS Organization
- Use role-specific classes for role-specific styling
- Leverage base classes for common patterns
- Keep specificity low to avoid conflicts
- Use CSS custom properties for consistent values

### 2. Component Development
- Start with base styles from `base.html`
- Add role-specific enhancements
- Test across different screen sizes
- Ensure accessibility compliance

### 3. Performance
- Minimize CSS file sizes
- Use efficient selectors
- Leverage CSS Grid and Flexbox
- Optimize for critical rendering path

### 4. Maintenance
- Document new components
- Follow naming conventions
- Test across all roles
- Update this guide when adding new patterns

## Common Patterns

### 1. Status Cards
```html
<div class="stat-card {{ role }}-primary">
    <div class="stat-number">{{ value }}</div>
    <div class="stat-label">{{ label }}</div>
</div>
```

### 2. Action Cards
```html
<div class="quick-action-{{ role }}">
    <div class="quick-action-{{ role }}-icon">
        <i class="bi bi-icon"></i>
    </div>
    <div class="quick-action-{{ role }}-title">{{ title }}</div>
    <div class="quick-action-{{ role }}-description">{{ description }}</div>
</div>
```

### 3. Status Indicators
```html
<span class="status-indicator-{{ role }} {{ status }}">
    {{ status_text }}
</span>
```

### 4. Modal Headers
```html
<div class="modal-header {{ role }}-modal">
    <h5 class="modal-title">{{ title }}</h5>
    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
</div>
```

## Troubleshooting

### Common Issues

1. **Styles Not Applying**
   - Check if role-specific CSS is loaded
   - Verify class names match role
   - Ensure proper CSS specificity

2. **Inconsistent Colors**
   - Use CSS custom properties
   - Check role-specific color variables
   - Verify color inheritance

3. **Responsive Issues**
   - Test on actual devices
   - Check breakpoint values
   - Verify viewport meta tag

4. **Performance Problems**
   - Minimize CSS file sizes
   - Use efficient selectors
   - Optimize critical CSS

## Future Enhancements

### Planned Improvements
- Dark mode support
- High contrast mode
- Additional role-specific themes
- Advanced animation library
- CSS-in-JS integration (if needed)

### Contributing
When adding new styles:
1. Follow existing patterns
2. Test across all roles
3. Update this documentation
4. Ensure accessibility compliance
5. Optimize for performance

---

**Last Updated**: [Current Date]
**Version**: 1.0
**Maintainer**: Development Team
