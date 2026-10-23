import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import eslint from 'eslint';

const app = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const linter = new eslint.ESLint({ cwd: app });
const ordinaryFile = 'src/calmframes/SeekGuardContractProbe.ts';
const guardedFile = 'src/calmframes/useFlashGuard.ts';

async function restrictedMessages(statement, filename = ordinaryFile) {
  const source = `export function attempt(player: {
    currentTime: number;
    fastSeek: (seconds: number) => void;
    setNativeProps: (props: object) => void;
  }) { ${statement} }`;
  const [result] = await linter.lintText(source, { filePath: path.join(app, filename) });
  assert.ok(!result.messages.some((message) => message.fatal), 'The contract probe must parse.');
  return result.messages.filter((message) =>
    message.ruleId === 'no-restricted-syntax' || message.ruleId === 'no-restricted-properties');
}

const seeks = [
  'player.currentTime = 1;',
  "player['currentTime'] = 1;",
  'player.currentTime += 1;',
  "player['currentTime'] -= 1;",
  'player.currentTime++;',
  '--player.currentTime;',
  "++player['currentTime'];",
  "player['currentTime']--;",
  'player.fastSeek(1);',
  "player['fastSeek'](1);",
];

for (const statement of seeks) {
  test(`refuses an unguarded seek: ${statement}`, async () => {
    const messages = await restrictedMessages(statement);
    assert.ok(messages.some((message) => message.ruleId === 'no-restricted-syntax' && message.severity === 2),
      `The seek guard must refuse ${statement}`);
  });
}

test('the guarded seek implementation retains its named exemption', async () => {
  assert.deepEqual(await restrictedMessages(seeks.join('\n'), guardedFile), []);
});

for (const filename of [ordinaryFile, guardedFile]) {
  for (const statement of ['player.setNativeProps({});', "player['setNativeProps']({});"]) {
    test(`still refuses setNativeProps in ${filename}: ${statement}`, async () => {
      assert.ok((await restrictedMessages(statement, filename)).some((message) => message.severity === 2));
    });
  }
}
