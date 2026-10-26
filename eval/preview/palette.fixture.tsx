/** Review-only exports from actual shared controls; no persistence or native access. */
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { Text, View } from 'react-native';
import fs from 'fs';
import path from 'path';
import CalmButton from '../../src/calmframes/CalmButton';
import CalmTouchable from '../../src/calmframes/CalmTouchable';
import { CALM_COLORS, CALM_TEXT } from '../../src/calmframes/calmStyles';
import { CalmControlAppearance, CONTROL_MATERIAL } from '../../src/calmframes/CalmControlSurface';
import { contrastRatio } from '../../src/calmframes/uiContrast';

test('export palette and actual control states with contrast floors', () => {
  const names = ['Primary', 'Focused', 'Pressed', 'Secondary', 'Selected', 'Disabled'];
  const view = render(<CalmControlAppearance.Provider value><View style={{ backgroundColor: CALM_COLORS.BACKGROUND, padding: 48, flex: 1 }}>
    <Text style={{ ...CALM_TEXT.section, color: CALM_COLORS.TEXT }}>Dusk coast · shared control states</Text>
    <View style={{ flexDirection: 'row', gap: 24, marginTop: 32 }}>
      {names.map((name, index) => <View key={name} style={{ width: 280 }}>
        <Text style={{ ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, marginBottom: 16 }}>{name}</Text>
        {name === 'Selected' ? <CalmTouchable testID="palette-selected" accessibilityRole="button" accessibilityState={{ selected: true }} style={{ borderWidth: 6, borderRadius: 18, minHeight: 88, justifyContent: 'center', paddingHorizontal: 26 }}><Text style={{ ...CALM_TEXT.control, color: CALM_COLORS.TEXT }}>✓ Everyone</Text></CalmTouchable>
          : <CalmButton testID={'palette-' + name} label={name === 'Secondary' ? 'Details' : 'Watch now'} primary={index < 3 || name === 'Disabled'} disabled={name === 'Disabled'} />}
      </View>)}
    </View>
  </View></CalmControlAppearance.Provider>);
  fireEvent(view.getByTestId('palette-Focused'), 'focus');
  fireEvent(view.getByTestId('palette-Pressed'), 'pressIn', {});
  const ratios = {
    pendingOnSlate: contrastRatio(CALM_COLORS.PENDING, CALM_COLORS.SURFACE),
    errorOnSlate: contrastRatio(CALM_COLORS.FAILED, CALM_COLORS.SURFACE),
    ivoryOnInk: contrastRatio(CALM_COLORS.TEXT, CALM_COLORS.BACKGROUND),
    secondaryTextOnInk: contrastRatio(CALM_COLORS.TEXT_DIM, CALM_COLORS.BACKGROUND),
    primaryMinimum: Math.min(...[...CONTROL_MATERIAL.primary, ...CONTROL_MATERIAL.primaryPressed].map(c => contrastRatio(CALM_COLORS.INK, c))),
    secondaryMinimum: Math.min(...[...CONTROL_MATERIAL.secondary, ...CONTROL_MATERIAL.secondaryPressed].map(c => contrastRatio(CALM_COLORS.TEXT_DIM, c))),
    selectedMinimum: Math.min(...CONTROL_MATERIAL.selected.map(c => contrastRatio(CALM_COLORS.TEXT_DIM, c))),
    disabled: contrastRatio(CALM_COLORS.TEXT_DISABLED, CONTROL_MATERIAL.disabled[0]),
    focusOnInkSeparator: contrastRatio(CALM_COLORS.FOCUS_RING, CALM_COLORS.INK),
    focusOnSelected: Math.min(...CONTROL_MATERIAL.selected.map(c => contrastRatio(CALM_COLORS.FOCUS_RING, c))),
  };
  for (const ratio of Object.values(ratios)) expect(ratio).toBeGreaterThanOrEqual(4.5);
  const out = path.resolve(__dirname, '../../build/dusk-palette-study'); fs.mkdirSync(out, { recursive: true });
  fs.writeFileSync(path.join(out, 'states.json'), JSON.stringify(view.toJSON(), null, 2));
  fs.writeFileSync(path.join(out, 'palette.json'), JSON.stringify({ colors: CALM_COLORS, materials: CONTROL_MATERIAL, contrast: ratios }, null, 2));
});
