# Native dimensional scene feasibility, 14 October 2026

Read-only assessment of candidate `ed1347ecb9773d38250a7b8bcc14cb2ee8641ab6`, Vega SDK 0.24.9914 and React Native 0.83. No dependencies, assets or app behavior changed for this assessment. No simulator access was retried. The separately requested Quiet Arcade browser prototype is a visual direction proof, not native compatibility evidence; its launch or completion was not observed here.

## Choice within the present constraints

Use an explicitly labelled **prerendered layered 2.5D native proof** for the first native scene. Build its dimensional appearance into original sculpted artwork: a rounded zen figure, contact shadows, materials, rim light and occlusion, then move independently rendered layers in response to remote focus. This supports limited parallax and discrete scene responses. It cannot supply free camera orbit, new viewpoints or physically correct real-time relighting.

A supported real-time 3D path is not established for this app's current runtime. Amazon's [Vega 0.24 library matrix](https://developer.amazon.com/docs/vega-api/0.24/supported-libraries) explicitly marks expo-gl unsupported for RN 0.83. Its RN 0.72 tab lists version 2.0.0. The [expo-gl API page](https://developer.amazon.com/docs/vega-api/0.24/expo-gl) describes a genuine GLView/OpenGL ES context but lists compatibility only through SDK 0.23/RN 0.72. These are different runtime targets, not a drop-in package recommendation.

[Vega WebGL documentation](https://developer.amazon.com/docs/vega/0.24/webview-webgl-best-practices) establishes WebGL 2.0 in Vega WebView, not the RN app's Hermes runtime. No expo-gl, Three.js, expo-three, React Three Fiber or WebView dependency is installed in this candidate. Browser Three.js/Spline compatibility cannot be assumed. A custom Fabric renderer/native graphics integration would be new platform work with an unproven compatibility and performance burden, outside this bounded UI task. SDK graphics headers alone do not establish a supported renderer integration.

## Available native tools

Installed Amazon packages: Reanimated 4.0.1+4.1.3, Worklets 1.0.1+0.6.0, SVG 3.0.9000000001+15.11.1, Lottie 3.0.9000000001+6.0.0-rc.1, linear-gradient 2.0.9000000001+2.6.2 and UI components 3.2.2. Image, Animated and View are already used in `HomeHarborScene.tsx`. Existing animation uses the native driver and stops on inactive lifecycle, reduced-motion or screen-reader state. New artwork should use this same policy.

Native transform types include perspective/rotateX/rotateY, but transforming a flat plane is not mesh rendering or real-time lighting. Prefer small translate/scale/opacity changes for a first layered proof. [Amazon's Reanimated page](https://developer.amazon.com/docs/vega-api/0.24/react-native-reanimated) supports RN 0.83 but excludes useReducedMotion, Fabric layout animations and CSS animations/transitions. Keep the existing AccessibilityInfo queries/events rather than using its unsupported reduced-motion hook. No setNativeProps.

`CalmTouchable.tsx` and `CalmButton.tsx` already expose native focus/blur and press. Installed `Libraries/TV/TVTypes.d.ts` declares directional/Select/Back events and next-focus targets. Keep accessible React Native controls as the input/focus layer and make decorative scene images inaccessible. No mouse-only hit testing, focus trapped in artwork or duplicate Select handling.

## Minimum proposed proof after direction approval

One Quiet Arcade vignette only, preserving the existing zen identity. Use original sculpted character and cabinet assets with baked soft shadows and rim lighting. Four cropped layers are sufficient: background, cabinet, character/shadow and foreground occluder. A second character pose or small sprite sequence can provide one deliberate response. No Amazon promotional artwork, paid assets, theme switcher, media/player modification or new onboarding.

Three observable states: still idle, focused object and selected response. D-pad moves among two native focus targets, with a clear outline and quiet depth shift of the associated object. Select on the zen figure gives one small pose response; Select on the cabinet changes one static scene state. No blinking, strobe, high-frequency glow or continuous forced camera drift. Back returns to the caller and restores its original focus.

Default to the still composition under existing household preferences. Reduced motion, screen reader, unknown accessibility state, inactive app or scene exit stops every animated layer. Controls and their accessible names remain functional with immediate state changes and a still fallback. The visual proof must be judged on the sculpted forms and lighting, not new typography or button decoration.

Native acceptance requires a matching package on the existing Vega Virtual Device: actual D-pad/Select/Back and return focus; a capture of the object response; lifecycle stop/resume; still fallback/reduced-motion behavior; VoiceView where available; frame pacing and image-memory observation. Browser screenshots or a working Three.js prototype do not pass those native checks. None of these native observations occurred in this assessment.

If the user requires true real-time 3D in the shipping native app, pause that implementation choice until a supported RN 0.83 rendering route is verified. Do not silently substitute 2.5D, downgrade the runtime, install libraries or migrate the app.
