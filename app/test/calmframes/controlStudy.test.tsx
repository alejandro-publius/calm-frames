/** Captures actual components with an opt-in material; all household state is ephemeral. */
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { StyleSheet, Text, View } from 'react-native';
import fs from 'fs';
import path from 'path';
import CalmButton from '../../src/calmframes/CalmButton';
import PinKeypad from '../../src/calmframes/PinKeypad';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import ParentAreaScreen from '../../src/calmframes/ParentAreaScreen';
import { CalmControlAppearance } from '../../src/calmframes/CalmControlSurface';
import { CALM_COLORS, CALM_TEXT, scale } from '../../src/calmframes/calmStyles';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { emptyHideLog } from '../../src/calmframes/hideLog';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import { checkedShelf } from './shelfFixtures';

jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
jest.mock('../../src/utils/pixelUtils', () => ({ ...jest.requireActual('../../src/utils/pixelUtils'), scaleUxToDp: (value: number) => Math.round(value * Number(process.env.CONTROL_STUDY_HEIGHT || 1080) / 1080) }));
const states = ['Default', 'Focus', 'Pressed', 'Disabled'];
const study = (children: React.ReactNode) => <CalmControlAppearance.Provider value>{children}</CalmControlAppearance.Provider>;
const height = Number(process.env.CONTROL_STUDY_HEIGHT || 1080);
const out = path.resolve(__dirname, '../../build/control-study', String(height));
const save = (name: string, tree: unknown) => { fs.mkdirSync(out, { recursive: true }); fs.writeFileSync(path.join(out, name + '.json'), JSON.stringify(tree, null, 2)); };

test('export four states through real shared controls, home and an in-memory settings group', () => {
  const matrix = render(study(<View style={styles.sheet}>
    <Text style={styles.heading}>Control surfaces</Text>
    <Text style={styles.note}>Implemented study · browser rendering · native pixels pending</Text>
    <View style={styles.columns}><View style={styles.rowLabel} />{states.map(state => <Text key={state} style={styles.column}>{state}</Text>)}</View>
    {['Primary', 'Secondary', 'Tertiary', 'Keypad'].map(kind => <View key={kind} style={styles.row}>
      <Text style={styles.rowLabel}>{kind}</Text>
      {states.map(state => <View key={state} style={styles.cell}>
        {kind === 'Keypad' ? <View><PinKeypad entered={0} idPrefix={`study-${kind}-${state}`} disabled={state === 'Disabled'} autoFocus={false} onDigit={jest.fn()} onDelete={jest.fn()} /></View>
          : <CalmButton testID={`study-${kind}-${state}`} primary={kind === 'Primary'} tertiary={kind === 'Tertiary'} quiet={kind === 'Tertiary'} label={kind === 'Primary' ? 'Watch now' : kind === 'Secondary' ? 'Details' : 'Back'} disabled={state === 'Disabled'} onPress={jest.fn()} />}
      </View>)}
    </View>)}
  </View>));
  for (const kind of ['Primary', 'Secondary', 'Tertiary', 'Keypad']) {
    const suffix = kind === 'Keypad' ? '-key-1' : '';
    fireEvent(matrix.getByTestId(`study-${kind}-Focus${suffix}`), 'focus');
    fireEvent(matrix.getByTestId(`study-${kind}-Pressed${suffix}`), 'focus');
    fireEvent(matrix.getByTestId(`study-${kind}-Pressed${suffix}`), 'pressIn', {});
  }
  // Isolate the first rendered keypad key without rebuilding or restyling the key.
  const isolateKeys = (value: unknown): unknown => {
    if (!value || typeof value !== 'object') return value;
    if (Array.isArray(value)) return value.map(isolateKeys);
    const node = value as { props?: { testID?: string }; children?: unknown[] };
    if (node.props?.testID?.endsWith('-keypad')) {
      const findKey = (part: unknown): unknown => {
        if (!part || typeof part !== 'object') return undefined;
        const item = part as { props?: { testID?: string }; children?: unknown[] };
        if (item.props?.testID?.endsWith('-key-1')) return item;
        for (const child of item.children || []) { const found = findKey(child); if (found) return found; }
        return undefined;
      };
      return findKey(node);
    }
    return { ...node, children: node.children?.map(isolateKeys) };
  };
  save('controls', isolateKeys(matrix.toJSON())); matrix.unmount();
  const home = render(study(<KidHomeScreen titles={checkedShelf()} onOpen={jest.fn()} onPlay={jest.fn()} onOpenParentArea={jest.fn()} />));
  save('home-default', home.toJSON());
  fireEvent(home.getByTestId('kid-home-watch'), 'focus'); save('home-focus', home.toJSON());
  home.unmount();

  const gate = setPin(emptyPinGate(), '1357', 'control-study-fixture', 4);
  const props = { gate, settings: DEFAULT_SETTINGS, log: emptyHideLog(), titles: checkedShelf(), onGateChange: jest.fn(), onSettingsChange: jest.fn(), onBack: jest.fn(), onSetPin: jest.fn(), nowMs: () => 1000 };
  const rows: unknown[] = [];
  for (const state of states) {
    const parent = render(study(<ParentAreaScreen {...props} />));
    for (const digit of '1357') fireEvent.press(parent.getByTestId(`parent-area-key-${digit}`));
    if (state === 'Disabled') parent.rerender(study(<ParentAreaScreen {...props} saving />));
    const selected = parent.getByTestId('parent-area-preset-wcag');
    expect(selected.props.accessibilityState.checked).toBe(true);
    if (state === 'Disabled') {
      expect(selected.props.accessibilityState.disabled).toBe(true);
      expect(StyleSheet.flatten(parent.getByText('✓ Chosen').props.style).color).toBe(CALM_COLORS.TEXT_DISABLED);
    }
    if (state === 'Focus' || state === 'Pressed') fireEvent(selected, 'focus');
    if (state === 'Pressed') fireEvent(selected, 'pressIn', {});
    const tree = parent.toJSON();
    const find = (value: unknown): unknown => {
      if (!value || typeof value !== 'object') return undefined;
      const node = value as { props?: { testID?: string }; children?: unknown[] };
      if (node.props?.testID === 'parent-area-preset-wcag') return node;
      for (const child of Array.isArray(value) ? value : node.children || []) { const found = find(child); if (found) return found; }
      return undefined;
    };
    rows.push({ state, tree: find(tree) });
    if (state === 'Default') {
      fireEvent(parent.getByTestId('parent-area-preset-broadcast'), 'focus');
      save('settings-group', parent.toJSON());
    }
    parent.unmount();
  }
  save('selected-rows', rows);
});

const styles = StyleSheet.create({
  sheet: { flex: 1, paddingHorizontal: scale(96), paddingTop: scale(54), backgroundColor: '#102F3A' },
  heading: { ...CALM_TEXT.screen, color: '#F3E8D3' },
  note: { ...CALM_TEXT.supporting, color: '#BDD0CF', marginTop: scale(12), marginBottom: scale(48) },
  columns: { flexDirection: 'row', alignItems: 'center', marginBottom: scale(24) },
  column: { ...CALM_TEXT.supporting, color: '#BDD0CF', width: scale(350) },
  row: { flexDirection: 'row', alignItems: 'center', minHeight: scale(175) },
  rowLabel: { ...CALM_TEXT.supporting, color: '#BDD0CF', width: scale(280) },
  cell: { width: scale(350) },
});
