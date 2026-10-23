# Pinned code excerpts

Read-only extracts from `13551e4`, which contains validated application source `d96c088`. These are partial implementation references, not new test results or a complete proof. Original paths and line spans are recorded for inspection.

## pipeline/verify.py

Lines 486 to 517; complete source SHA-256 `2faaa2a59a3d4a5dc951e3f32c24741436ce801faa91e55f9d9667df66ec6c28`.

```python
def verify_title(
    layout: TitleLayout,
    *,
    source: str | Path,
    presets: Sequence[str],
    adapter: FlashmapAdapter,
    pub_key: str | Path | None,
    diag_in: float | None = None,
    distance_ft: float | None = None,
    calm_margin_ms: float = DEFAULT_CALM_MARGIN_MS,
    rerender_cover_model: bool = True,
    playback_compatible: bool | None = None,
) -> VerifyReport:
    source = Path(source)
    report = VerifyReport(
        sha256=layout.sha256,
        source_path=str(source),
        presets=list(presets),
        started_at=time.time(),
    )

    # 1. The source is the file this title was built from.
    if not source.exists():
        report.add("source_present", False, f"source file is missing: {source}")
        report.finished_at = time.time()
        return report
    actual_sha = sha256_file(source)
    report.add(
        "source_hash",
        actual_sha == layout.sha256,
        f"source hashes to {actual_sha}, title is filed under {layout.sha256}",
        actual=actual_sha,
```

## pipeline/packaged_library.py

Lines 437 to 467; complete source SHA-256 `ce271fc2eede41e5414b38dc1514989d28b50911b3c6df5ab06c9ba09cdc29bb`.

```python
def export_packaged_library(workdir: str | Path, output: str | Path, *, pub: str | Path,
                           source_shas: Sequence[str] | None = None) -> dict:
    root, destination = _root(workdir), _root(output)
    if destination == root or destination.is_relative_to(root) or root.is_relative_to(destination):
        raise PackagedLibraryError("The package output and preparation workspace must be separate.")
    public = load_public_key(pub)
    public_raw = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    selected = set(source_shas) if source_shas is not None else None
    if selected is not None and (not selected or any(not _SHA.fullmatch(sha) for sha in selected)):
        raise PackagedLibraryError("Select complete source SHA-256 identifiers.")
    destination.mkdir(parents=True, exist_ok=True)
    with local._lock(root), local._lock(destination):
        _check_output_root(destination)
        catalog = local._snapshot(root)
        receipts = [item for item in catalog["titles"] if selected is None or item["source_sha256"] in selected]
        if selected is not None and {item["source_sha256"] for item in receipts} != selected:
            raise PackagedLibraryError("A selected title has no current verified local receipt.")
        if not receipts or len(receipts) > MAX_TITLES:
            raise PackagedLibraryError("Export between one and sixteen verified local titles.")
        with tempfile.TemporaryDirectory(prefix=".stage-", dir=destination) as temporary:
            staged = Path(temporary)
            files: dict[str, dict] = {}
            titles: list[dict] = []
            reports: dict[str, bytes] = {}
            total = 0
            for receipt in receipts:
                title, size = _title(receipt, root, staged, public, files, reports)
                total += size
                if total > MAX_BUNDLE_BYTES:
                    raise PackagedLibraryError("The prepared library exceeds the package byte budget.")
                titles.append(title)
```

## app/src/calmframes/packagedLibrary.ts

Lines 244 to 252; complete source SHA-256 `fc10728d6d28f878366953f290f09448fbc88f68316f98f4a44e15a20f048a9b`.

```tsx
  const match = (title: CatalogTitle, settings: HouseholdSettings) =>
    titles(settings).find((expected) => expected.id === title.id &&
      expected.uri === title.uri && expected.sha256 === title.sha256 &&
      expected.durationMs === title.durationMs &&
      expected.renditionSha256 === title.renditionSha256 &&
      expected.renditionStartOffsetMs === title.renditionStartOffsetMs &&
      sameMaps(title.maps, expected.maps) &&
      JSON.stringify(title.textTrack) === JSON.stringify(expected.textTrack));
  return {
```

## app/src/calmframes/useFlashGuard.ts

Lines 382 to 420; complete source SHA-256 `45a7a9140b564c7885bae6d0b238e1644e15cff6b457cb4603056abaae419b40`.

```tsx
  // The schedule itself, on the harness that GATE 1 measured.
  const harness = useCoverHarness(mediaRef, {
    mode: activeStatus === 'verified' && ready ? 'timing' : 'off',
    intervals,
    foreground,
    ready,
    scheduleLabel: `flash-guard:${titleId}`,
    onUncertainty: latchSceneAt,
  });

  const seekEngine = useMemo(
    () =>
      createSeekEngine({
        getIntervals: () => intervalsRef.current,
        getDurationMs: () => durationMs,
        onPlan: (plan) => {
          latchSceneAt(plan.targetMs);
          latchSceneInterval(plan.interval);
          setSceneSeekDisruptions((count) => count + 1);
        },
        setCover: (covered, reason) => {
          trace('seek', JSON.stringify({ phase: 'cover-request', covered, reason }));
          setSeekHolding(covered);
        },
        seekTo: (targetMs) => {
          const element = mediaRef.current as
            | (MediaElementLike & { currentTime?: number })
            | null;
          if (element) {
            trace('seek', JSON.stringify({ phase: 'playhead-write', targetMs }));
            element.currentTime = targetMs / 1000;
          }
        },
        announce: (text) => announceForAccessibility(text),
      }),
    // A new engine per title, not per render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [durationMs, mediaRef, titleId],
  );
```

## app/src/calmframes/PlaybackProofPanel.tsx

Lines 10 to 55; complete source SHA-256 `23d55ab62ac4429c17894ff7a180b18b9909b856dae171cfb8d48728438d3759`.

```tsx

export default function PlaybackProofPanel({ entry, settings, testID = 'playback-proof' }: {
  entry: CheckedTitle; settings: HouseholdSettings; testID?: string;
}) {
  const [stage, setStage] = React.useState<'source' | 'prepared' | 'binding'>('source');
  const proof = playbackProofFor(entry, settings);
  if (!proof) return <View testID={`${testID}-unavailable`} style={styles.stage}>
    <Text accessibilityRole="header" style={styles.heading}>Playback proof unavailable</Text>
    <Text style={styles.line}>No matching report summary is available for this selection. This page cannot confirm its measurements.</Text>
  </View>;
  const findings = buildCoverIntervals(entry.segments, { guardBandMs: 0, minCoverMs: 0, durationMs: proof.durationMs });
  const covered = buildCoverIntervals(entry.segments, { ...coverOptionsFor(settings), durationMs: proof.durationMs });
  const profileLabel = (name: string) => name === 'wcag' ? 'WCAG' : name === 'broadcast' ? 'Broadcast' : 'Extra cautious';
  return <View testID={testID} style={styles.record}>
    <Text accessibilityRole="header" style={styles.heading}>Playback proof</Text>
    <Text style={styles.line}>{`${PRESETS[settings.preset].title} · ${(proof.durationMs / 1000).toFixed(1)} seconds · selected video edition`}</Text>
    <View style={styles.steps}>
      {(['source', 'prepared', 'binding'] as const).map((step, index) => <CalmButton key={step} quiet
        testID={`${testID}-step-${step}`} label={`${index + 1} · ${step === 'binding' ? 'Selection' : step === 'source' ? 'Source' : 'Prepared'}`}
        accessibilityLabel={`${step === 'binding' ? 'Selection' : step === 'source' ? 'Source' : 'Prepared'} evidence${stage === step ? ', selected' : ''}`}
        onPress={() => setStage(step)} />)}
    </View>
    {stage === 'source' ? <View style={styles.stage} testID={`${testID}-source`}>
      <Text style={styles.label}>1 · Source measured</Text>
      <Text style={styles.metric}>{`${findings.length} flagged period${findings.length === 1 ? '' : 's'}`}</Text>
      <Text style={styles.line}>Overlapping source findings are counted once. The original video is not played here.</Text>
      {proof.source.map(item => <Text key={item.profile} style={styles.line}>{`${profileLabel(item.profile)} map: ${item.findings} findings · ${item.analyzer ?? 'analyzer version not recorded'}`}</Text>)}
    </View> : stage === 'prepared' ? <View style={styles.stage} testID={`${testID}-prepared`}>
      <Text style={styles.label}>2 · Prepared file checked</Text>
      {proof.output.map(item => <Text key={item.profile} style={styles.metric}>{`${profileLabel(item.profile)}: ${item.findings === null ? 'finding count not recorded' : `${item.findings} output findings`}`}</Text>)}
      <Text style={styles.line}>{`${covered.length} covered period${covered.length === 1 ? '' : 's'} · ${(totalCoveredMs(covered) / 1000).toFixed(1)} seconds including margins`}</Text>
      <Text style={styles.line}>{proof.outcome === 'no flagged segments'
        ? 'Nothing was flagged, so this result does not demonstrate a cover working.'
        : proof.outcome === 'cover proven drawn' ? 'The report verifies that the replacement picture was drawn.' : 'The report does not prove that the cover was drawn.'}</Text>
      <Text style={styles.line}>{proof.timingPreserved && proof.frameCount !== null
        ? `${proof.frameCount} frames · frame timing checked against the source`
        : 'Complete frame-timing measurements are not recorded in this summary.'}</Text>
      {proof.output.map(item => <Text key={item.profile} style={styles.line}>{`${profileLabel(item.profile)} output analyzer: ${item.analyzer ?? 'version not recorded in this report'}`}</Text>)}
    </View> : <View style={styles.stage} testID={`${testID}-binding`}>
      <Text style={styles.label}>3 · Selection matches</Text>
      <Text style={styles.line}>The selected edition and signed timing maps match the approved file record. Media bytes are checked when the app is built; this page does not rescan the video.</Text>
      <Text style={styles.identifier}>{`Prepared file ${proof.renditionSha256.slice(0, 12)} · report ${proof.reportSha256.slice(0, 12)}`}</Text>
    </View>}
    <Text style={styles.line}>These checks do not establish personal comfort or medical safety. Detection can miss flashing. The full record below explains the limits.</Text>
  </View>;
}
```

## app/src/calmframes/ReadingStop.tsx

Lines 24 to 40; complete source SHA-256 `ea408665a263c8b8ab559e361dc2a0a95be291db3acd2afdad3f1a816467b154`.

```tsx
export default function ReadingStop({ testID, style, children }: {
  testID: string; style?: StyleProp<ViewStyle>; children: React.ReactNode;
}) {
  const coastal = React.useContext(CoastalAppearance);
  const colors = coastal ? COASTAL_COLORS : CALM_COLORS;
  const [focused, setFocused] = React.useState(false);
  return <CalmControlAppearance.Provider value={false}>
    <TouchableOpacity testID={testID} accessibilityRole="text" activeOpacity={1}
      // React Native makes a touchable focusable only when it has a press handler.
      onPress={() => undefined}
      onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
      style={[styles.stop, style, focused ? { borderColor: colors.FOCUS_RING, backgroundColor: colors.SURFACE_FOCUSED } : null]}>
      {children}
    </TouchableOpacity>
  </CalmControlAppearance.Provider>;
}

```
