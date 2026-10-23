# Bounded cache and Back review, October 17, 2026

GO for an owner-approved native checkpoint. Review target:
33cbf2980be689ee7e32fc7e8e8534e14a5ca712. No installation is authorized by this
review. An independent read-only local reviewer found no blocking regression.
The parent review added 16 adversarial cases; the affected three suites pass all
37 tests, with typecheck and targeted lint passing. No runtime repair was needed.

The cache is keyed by exact complete text, including signature, signer metadata,
algorithm, version, source and map content; its value is the exact trusted public
key. Parse/version/algorithm/key checks precede a hit. Source SHA, current expiry
policy and structure checks follow it. Neither filename nor signature key_id is
a trust anchor. The key_id is existing descriptive metadata; its label alone cannot
authorize a changed signer. Exact route matching selects the compiled trusted key.
Rotation or removal of that supplied key rejects previously authenticated text.
There is no separate remote revocation service in this API, before or after this
change. Cached authentication is not permission to bypass the caller's current key.

Rejected signatures are never cached. Cryptographically authenticated text rejected
later for expiry, file identity or malformed structure may retain authentication,
but the refusal is recomputed every time. Tests cover that distinction, changed
signatures/payload/intervals/algorithms/versions, changed trust, clock expiry, file
identity, result mutation, FIFO eviction, large uncached maps, interleaved callers
and module reload. Synthetic signing keys exist only in test memory.

Verification is synchronous with no await or shared in-flight verdict. The private
module-local cache retains at most eight texts, each no more than 64K characters,
plus public keys. Every call returns freshly parsed objects. Reload creates an empty
cache. Supported algorithm/version and verifier code are fixed for a loaded module;
there is no live verifier replacement or persisted authentication store.

Back detaches both native surfaces before requesting synchronous teardown. Fast exit
is reached only after teardown returns true, which requires native deinitializeSync
to return the literal success result. Timeout/failure/throw do not report success;
they retain the prior 700 ms fallback. Tests assert detachment and teardown return
precede navigation, with repeated actions leaving only once. Pending initialization
already checks media-instance identity before loading. No new frame exposure path
was found in source. Native compositor behavior and zero stale visible frames still
require the approved native checkpoint; unit tests do not establish them.

The earlier failure branch reference clearing and delayed exit predate this change.
No media, trust configuration, detector, package or installed app changed.
