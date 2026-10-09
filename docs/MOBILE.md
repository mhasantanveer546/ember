# Mobile app (Phase 7)

## 7.1 Concepts
- **React Native** renders real native views (`View`, `Text`, `Pressable`) instead of HTML. There is no CSS: styles are JS objects, layout is flexbox (column by default), and text must live inside `<Text>`.
- **Expo** is the toolchain on top: one command (`npx expo start`) runs the app on a phone via **Expo Go** with no Android Studio/Xcode; **EAS Build** later produces installable Android/iOS binaries in the cloud.
- **Expo Router** gives file-based navigation: `app/(tabs)/search.tsx` is the Search tab; `app/document/[id].tsx` is a screen with a route parameter; `(auth)` / `(tabs)` are route groups (don't appear in URLs).
- **API access** is the same HTTP/JSON as the web: bearer access token + rotating refresh token. The client in `src/services/apiClient.ts` mirrors the web client (single-flight refresh, friendly errors).
- **Storage:** tokens go in the OS secure store (`expo-secure-store` = iOS Keychain / Android Keystore), not AsyncStorage (unencrypted).
- **Platform differences handled:** Android emulator reaches the host at `10.0.2.2`; `ActionSheetIOS` vs `Alert` for menus; KeyboardAvoidingView only on iOS.

## 7.5 Upload and permissions
Files are chosen with the **system document picker** (iOS Files / Android Storage Access Framework). The user grants access to only the files they select, so Ember requests no storage permission. Checks run client-side for fast feedback (type, 25 MB, empty) and again on the server (extension, MIME, magic bytes, size). Uploads use `XMLHttpRequest` so progress can be shown.

## Decisions
| Decision | Choice | Why |
|---|---|---|
| Navigation | Expo Router | Official, file-based, deep links for free |
| Expo vs bare RN | Expo (managed) | No native toolchain needed; can eject later |
| Token storage | SecureStore | Encrypted at rest |
| Preview of document | Extracted text with highlights | The backend stores text, not page images (PDF page rendering is a later feature) |

## Verified / not verified
- Verified here: TypeScript strict passes; Metro compiles Android and iOS bundles; the same code run in a browser against the real API (sign-in, home, search with highlights, document find/next/prev, knowledge list, profile).
- **Not verified here:** running on a physical phone/emulator (no device in the build environment), the native file picker, and push of large uploads over mobile networks. Please test those on your device.

## Not built yet
Web search, bookmarks, "Ask Ember" chat, PDF page thumbnails (shown in the product mockup; they need later backend phases), offline mode, biometric lock, EAS builds and store submission.
