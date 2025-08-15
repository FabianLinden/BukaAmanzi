# Enhanced UI Components

This directory contains a comprehensive set of enhanced UI components designed for the Buka Amanzi Water Watch System. All components feature smooth animations, professional styling, and accessibility considerations.

## Components Overview

### Button
Enhanced button component with multiple variants, sizes, and animation states.

**Features:**
- Multiple variants: primary, secondary, outline, ghost, gradient, success, warning, danger
- Sizes: xs, sm, md, lg, xl
- Loading states with spinner
- Icon support (left/right positioning)
- Hover animations and scaling effects
- Full width option

**Usage:**
```tsx
import { Button } from './ui/Button';

<Button variant="primary" size="md" icon={<Icon />}>
  Click me
</Button>
```

### Card
Flexible card component with multiple variants and animation support.

**Features:**
- Variants: default, elevated, glass, gradient, minimal
- Customizable padding and border radius
- Hover effects and animations
- Modular header, content, and footer components

**Usage:**
```tsx
import { Card, CardHeader, CardContent, CardFooter } from './ui/Card';

<Card variant="glass" hoverEffect>
  <CardHeader title="Title" subtitle="Subtitle" />
  <CardContent>Content here</CardContent>
  <CardFooter>Footer content</CardFooter>
</Card>
```

### Input
Professional input component with validation and animation states.

**Features:**
- Multiple variants: default, filled, outlined, minimal
- Icon support with positioning
- Error and helper text display
- Focus animations and state management
- Full width option

### Modal
Accessible modal component with smooth animations.

**Features:**
- Multiple sizes: sm, md, lg, xl, full
- Backdrop blur and overlay effects
- Keyboard navigation (ESC to close)
- Smooth enter/exit animations
- Modular header, body, and footer

### Badge & Status Components
Versatile badge system for status indicators and labels.

**Features:**
- Multiple variants with color coding
- Status-specific badges for project states
- Priority badges for importance levels
- Pulse animations for active states
- Icon support

### ProgressBar
Enhanced progress bar with multiple visual styles.

**Features:**
- Animated progress transitions
- Multiple variants with status-based coloring
- Striped and glow effects
- Size variations
- Status indicators and labels

### Tooltip
Accessible tooltip component with positioning options.

**Features:**
- Four position options: top, bottom, left, right
- Multiple trigger types: hover, click, focus
- Smooth animations
- Arrow indicators
- Specialized variants (info, warning, error, success)

### Loading Components
Comprehensive loading system with multiple animation styles.

**Features:**
- Multiple variants: spinner, dots, pulse, wave, water
- Skeleton loading for content placeholders
- Full screen and overlay modes
- Loading overlay wrapper component
- Size and color customization

## Animation System

All components use a consistent animation system based on Tailwind CSS classes:

- `animate-fade-in` - Smooth fade in effect
- `animate-slide-in-*` - Directional slide animations
- `animate-scale-in` - Scale up animation
- `animate-gentle-bounce` - Subtle bounce effect
- `animate-smooth-pulse` - Gentle pulsing
- `animate-water-flow` - Water-themed flowing animation

## Design Principles

1. **Consistency** - All components follow the same design language
2. **Accessibility** - ARIA labels, keyboard navigation, focus management
3. **Performance** - Optimized animations and minimal re-renders
4. **Flexibility** - Extensive customization options
5. **Water Theme** - Consistent with the application's water monitoring theme

## Color Palette

The components use a water-inspired color palette:
- Primary: water-blue (various shades)
- Secondary: ocean and aqua tones
- Status colors: emerald (success), amber (warning), red (danger)
- Neutral: gray scale for text and borders

## Best Practices

1. Use semantic variants (success, warning, danger) for status-related UI
2. Combine components for complex interfaces (Card + Button + Badge)
3. Leverage the animation system for smooth user experiences
4. Use loading states for better perceived performance
5. Implement proper error handling with Input validation
6. Use tooltips for additional context without cluttering the UI

## Customization

All components accept className props for additional styling and can be extended with Tailwind CSS classes. The design system is built to be flexible while maintaining consistency.
