/**
 * The manifest, which the build rewrites.
 *
 * `react-native build-kepler` rewrites app/manifest.toml on every build, adding
 * a [[needs.module]] entry for each installed @amazon-devices package. Two
 * things in that file are load bearing and easy to lose in a rewrite:
 *
 * - the IMediaPlaybackServer extras block, which is how Alexa and the remote's
 *   transport commands reach the app at all. Without it, SafeMediaControlHandler
 *   is never called and a spoken "skip forward" goes straight past the guard;
 * - the accessibility privilege, without which no VoiceView announcement is
 *   made.
 *
 * So they get a test. The original block is at commit cf8b752 in this repo's
 * history if it ever has to be restored by hand.
 */

import fs from 'fs';
import path from 'path';

const manifest = fs.readFileSync(
  path.join(__dirname, '..', '..', 'manifest.toml'),
  'utf8',
);

describe('app/manifest.toml', () => {
  it('opts in to the Vega Media Controls transport commands', () => {
    expect(manifest).toContain(
      'interface_name = "com.amazon.kepler.media.IMediaPlaybackServer"',
    );
    for (const command of [
      'StartOver',
      'Previous',
      'Next',
      'SkipForward',
      'SkipBackward',
    ]) {
      expect(manifest).toMatch(new RegExp(`"${command}"`));
    }
    // AdvancedSeek is what lets a spoken seek carry a position rather than a
    // direction, so handleSeek gets a target to check.
    expect(manifest).toMatch(/features = \[[^\]]*"AdvancedSeek"/);
  });

  it('declares the media category on the main component', () => {
    expect(manifest).toContain('com.amazon.category.kepler.media');
  });

  it('asks for the accessibility privilege that VoiceView announcements need', () => {
    expect(manifest).toMatch(
      /\[\[wants\.privilege\]\]\s*\nid = "com\.amazon\.devconf\.privilege\.accessibility"/,
    );
  });

  it('has no task or service components, which can crash at launch on RN 0.83', () => {
    expect(manifest).not.toContain('[[components.task]]');
    expect(manifest).not.toContain('[[components.service]]');
  });

  it('uses a package id developer mode will sideload', () => {
    const id = /^id = "(.+)"/m.exec(manifest.split('[package]')[1] ?? '');
    expect(id?.[1]).toBeDefined();
    expect(id?.[1]?.startsWith('com.amazon')).toBe(false);
  });
});
