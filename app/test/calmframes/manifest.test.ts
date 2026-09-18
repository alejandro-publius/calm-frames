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

  it('points at an icon that is there, and is the size Amazon asks for', () => {
    // The packaging tool does not check this. Strings in vpt show it validates
    // the @image/ name and whether the file exists, and a missing file is only
    // a warning: "icon validation is not enforced, continuing packaging".
    // There is no size check in it at all, so a wrong icon would sail through
    // the build and be caught at Appstore review instead. Hence this.
    //
    // The numbers come from the 0.24 manifest page: "Required resolution and
    // format: 512x512, PNG" and "Maximum file size: 1MB".
    const declared = /^icon = "(.+?)"/m.exec(manifest.split('[package]')[1] ?? '');
    expect(declared?.[1]).toBeDefined();

    const name = declared![1].replace(/^@image\//, '');
    expect(name).not.toBe(declared![1]);

    const file = path.join(__dirname, '..', '..', 'assets', 'image', name);
    expect(fs.existsSync(file)).toBe(true);

    const bytes = fs.readFileSync(file);
    expect(bytes.subarray(0, 8)).toEqual(
      Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    );
    // IHDR is the first chunk of every PNG: width and height are the four byte
    // big endian pair at offset 16.
    expect(bytes.readUInt32BE(16)).toBe(512);
    expect(bytes.readUInt32BE(20)).toBe(512);
    expect(bytes.byteLength).toBeLessThan(1024 * 1024);
  });
});
