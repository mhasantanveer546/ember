# Ember mobile (Expo / React Native)

Phase 7: the phone app. It talks to the **same FastAPI backend** as the web app (same endpoints, same auth, same search).

## Run it on your phone (Expo Go)
```bash
cd mobile
cp .env.example .env            # then edit EXPO_PUBLIC_API_URL (see below)
npm install
npx expo start                  # scan the QR code with Expo Go (Android) or the Camera app (iOS)
```
`EXPO_PUBLIC_API_URL` depends on where the API runs:

| Where you run the app | Value |
|---|---|
| Physical phone + API on your PC | `http://<your-PC-LAN-IP>:8000` (find it with `ipconfig`); start the API with `--host 0.0.0.0`; phone and PC on the same Wi-Fi; allow Python through Windows Firewall |
| Android emulator | `http://10.0.2.2:8000` |
| iOS simulator (Mac) | `http://localhost:8000` |
| Deployed API | `https://<your-service>.onrender.com` (see `docs/DEPLOYMENT.md`) |

Restart `npx expo start` after changing `.env` (values are inlined at build time). Plain `http://` works in development only; use `https` for anything you ship.

If Expo Go says the project is incompatible, update Expo Go from the store (this project uses Expo SDK 57).

## Scripts
`npm run typecheck`, `npm run bundle:check` (compiles the Android + iOS bundles with Metro, no device needed), `npm run web` (browser preview of the same code).

## Structure
```
app/                 Expo Router screens (file = route)
  (auth)/            login, register
  (tabs)/            Home, Search, Knowledge, Profile
  document/[id]      reader with find + match navigation + text size
  history, workspaces/
src/
  services/          apiClient (auth, refresh, errors, upload progress) + auth/workspaces/documents/search
  context/           Auth, Workspace
  components/        ui primitives, SearchInput (autocomplete), Snippet, Logo, HeroArt
  lib/               secure token store, config, formatting, highlighting
```
See `docs/MOBILE.md` for the concepts, decisions and security notes.
