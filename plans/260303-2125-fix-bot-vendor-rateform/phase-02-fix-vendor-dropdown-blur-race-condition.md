# Phase 2: Fix Vendor Dropdown Blur/Click Race Condition

## Context Links
- Vendor dropdown: `frontend/src/App.jsx` (lines 1077-1162)
- onBlur handler: line 1093-1100
- onClick handlers: lines 1129, 1151

## Overview
- **Priority**: P1 (vendor assignment broken on some devices)
- **Status**: pending
- **Description**: Dropdown items use `onClick` which fires AFTER `onBlur`. The `onBlur` hides the dropdown via `setTimeout(200ms)` which is unreliable across devices/browsers. Fix: use `onMouseDown` + `e.preventDefault()` which fires BEFORE blur and prevents focus loss.

## Key Insights
- `onMouseDown` fires before `onBlur` in all browsers
- `e.preventDefault()` on mousedown prevents the input from losing focus
- This is the standard pattern for custom dropdowns in React
- The "-- Bo chon --" item (line 1127-1134) also needs the same fix

## Requirements
### Functional
- Clicking a vendor in dropdown selects it reliably
- Clicking "-- Bo chon --" clears vendor reliably
- Dropdown still closes after selection
- Search/filter still works

### Non-functional
- No setTimeout race conditions
- Works on all devices (desktop, tablet, mobile)

## Related Code Files
- **Modify**: `frontend/src/App.jsx` (lines 1127-1160)

## Implementation Steps

### 1. Fix "-- Bo chon --" item (line 1127-1134)

**Current** (line 1129):
```jsx
onClick={() => {
```

**Change to**:
```jsx
onMouseDown={(e) => {
  e.preventDefault()
```

The rest of the handler body stays the same.

### 2. Fix vendor list items (line 1151-1156)

**Current** (line 1151):
```jsx
onClick={() => {
```

**Change to**:
```jsx
onMouseDown={(e) => {
  e.preventDefault()
```

The rest of the handler body stays the same.

### 3. Simplify onBlur handler (optional improvement)

The `setTimeout` at line 1095 can be removed or reduced since `onMouseDown` + `preventDefault` prevents blur when clicking dropdown items. However, keeping a small delay is fine for edge cases (clicking outside).

**Current** (lines 1093-1100):
```jsx
onBlur={() => {
  setTimeout(() => {
    setServices(prev => prev.map(s =>
      s.svc_id === svc.svc_id ? { ...s, showVendorDropdown: false } : s
    ))
  }, 200)
}}
```

**Keep as-is** for safety. The `onMouseDown` + `preventDefault` fix is sufficient. The `setTimeout` only fires when user clicks outside the dropdown (legitimate blur), which still works correctly.

## Exact Code Changes

### Change 1: Line 1129

**old_string**:
```
                  onClick={() => {
                    handleAssign(svc.svc_id, null, svc.employee_id || null)
```

**new_string**:
```
                  onMouseDown={(e) => {
                    e.preventDefault()
                    handleAssign(svc.svc_id, null, svc.employee_id || null)
```

### Change 2: Line 1151

**old_string**:
```
                                    onClick={() => {
                                      handleAssign(svc.svc_id, v.vendor_id, svc.employee_id || null)
```

**new_string**:
```
                                    onMouseDown={(e) => {
                                      e.preventDefault()
                                      handleAssign(svc.svc_id, v.vendor_id, svc.employee_id || null)
```

## Todo List
- [ ] Change "-- Bo chon --" from onClick to onMouseDown+preventDefault
- [ ] Change vendor items from onClick to onMouseDown+preventDefault
- [ ] Test: click vendor in dropdown selects it
- [ ] Test: click "-- Bo chon --" clears vendor
- [ ] Test: clicking outside dropdown still closes it

## Success Criteria
- Vendor dropdown selection works 100% reliably on first click
- No race condition between blur and click

## Risk Assessment
- **Very low**: `onMouseDown` + `preventDefault` is standard React dropdown pattern
- **No regressions**: onBlur still works for clicking outside

## Security Considerations
- N/A (UI-only change)
