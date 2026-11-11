# Pebble Index 01 — Independent Web UI Reconstruction

> **Project type:** browser-based UI study / interactive prototype  
> **Target:** Pebble Index 01 companion experience  
> **Platform:** Web (desktop-first, responsive mobile layout)  
> **Scope:** UI and interaction reconstruction, not firmware or protocol emulation  
> **Status:** runnable prototype; demo data; no physical-ring connection  
> **Relationship:** independent, unofficial project; not affiliated with Core Devices or Pebble

## 1. Purpose and scope

This repository implements a browser UI inspired by the publicly documented user-facing workflows of Pebble Index 01. It is intended for product exploration, interaction prototyping, design-system experiments, and frontend development.

The Index 01 product is a button-and-microphone ring. The ring captures audio while its button is held and transfers recordings to the Pebble mobile app over Bluetooth. The companion app is responsible for transcription, interpreting the user's intent, organizing notes and reminders, displaying the Index feed, and optionally routing content to integrations. This web project reconstructs a subset of the *companion experience* as a local browser prototype.

### In scope

- Index-style activity feed and recording detail view.
- Quick text capture and simulated voice capture.
- Feed search and type filters.
- Notes library/list overview.
- Todo/reminder checklist with completion state.
- Settings information architecture and illustrative preference controls.
- Local browser persistence using `localStorage`.
- JSON export of demo content.
- Responsive desktop and mobile layouts.
- Seed data to make the interface useful immediately.

### Explicitly out of scope

- BLE scanning, pairing, GATT communication, ring firmware, audio transfer, or device authentication.
- Actual microphone capture or speech recognition.
- Real transcription, AI agent execution, web search, reminders/alarms, calendar writes, music controls, or notifications.
- Real webhook delivery, MCP client/server communication, plugins, OAuth, account sign-in, encrypted cloud backup, or cross-device sync.
- Exact reproduction of proprietary assets, source code, or non-public interfaces.

This is a UI reconstruction based on public documentation and product behavior, not a claim of source-level equivalence.

## 2. Reference research and evidence

The implementation's information architecture is based on these public references:

1. **Pebble Index 01 developer overview** — explains the ring/app responsibility split, gestures, processing options, and extension points: <https://developer.repebble.com/index-01/>
2. **Pebble mobile app developer page** — identifies the official companion application and its open-source Kotlin Multiplatform architecture: <https://developer.repebble.com/mobile-app/>
3. **Official mobile app repository README** — documents the public mobile app modules, including `experimental`, `index-ai`, and `libindex`: <https://github.com/coredevices/mobileapp>
4. **Index 01 getting-started guide** — documents the Index feed, recording details, Todos, Notes, text capture, speech-recognition choices, and backups: <https://help.repebble.com/en/articles/15434751-index-01-getting-started-guide>
5. **Advanced features guide** — documents webhook and MCP concepts: <https://help.repebble.com/en/articles/15724406-index-advanced-features-mcp-webhook>
6. **Index FAQ** — useful for feed behavior, pairing guidance, and expected transfer/transcription timing: <https://help.repebble.com/en/articles/15900461-index-01-faq-and-tips>

### Evidence labels used in this project

| Label | Meaning |
|---|---|
| Publicly documented | Directly described in a linked Pebble developer/help reference. |
| UI interpretation | A visual or interaction decision made to produce a coherent web experience. |
| Demo-only | Local mock behavior; does not call a Pebble service or hardware. |
| Not implemented | Intentionally absent, usually because a web browser cannot reproduce the native capability in this project. |

The app is intentionally explicit about demo mode and disconnected hardware state.

## 3. Feature inventory

| Feature | Prototype behavior | Evidence / qualification |
|---|---|---|
| Index feed | Chronological activity list; click row for details | Feed and recording detail are documented |
| Text capture | Enter text; creates a local feed entry | Official app supports typing into the Index home view |
| Voice capture | Dialog accepts typed sample transcript | Simulates a voice note; no microphone/STT |
| Feed search | Client-side substring search | UI interpretation |
| Feed filter | All / Notes / Reminders / Answers | Derived from documented action categories |
| Todos | Add and check off local reminders | Built-in reminders/Todos are documented |
| Notes | Note-list overview and add-list interaction | Notes and lists are documented |
| Settings | Illustrative speech/agent/action/backup choices | Underlying setting categories are documented |
| Export | Downloads a JSON snapshot | Prototype-specific convenience |
| Persistence | `localStorage` | Prototype-specific; not the official backup mechanism |

## 4. Architecture

The prototype is a small Vite application with no backend.

```text
Browser
└── index.html
    ├── src/style.css       Design tokens, responsive layout, components
    └── src/main.js         State, rendering, event handlers, local persistence
        └── localStorage    Demo-only persistence
```

### Runtime data model

A feed entry has this shape:

```json
{
  "id": 1731264120000,
  "time": "10:42 AM",
  "date": "Today",
  "type": "note",
  "title": "Ideas for the studio refresh",
  "body": "Try a warmer palette...",
  "action": "Added to Notes · Studio"
}
```

Supported `type` values:

- `note`: content filed into a note list.
- `reminder`: reminder-like feed item.
- `answer`: answer-like feed item.

Todo item:

```json
{ "id": 1, "text": "Review the studio moodboard", "done": false }
```

Note-list item:

```json
{ "name": "Studio", "count": 4, "desc": "Ideas and references..." }
```

### State and persistence

The application loads three keys:

- `index-demo-entries`
- `index-demo-todos`
- `index-demo-notes`

If a key does not exist or contains invalid JSON, the built-in seed data is used. State changes are serialized back to local storage. Data is scoped to the browser origin and profile. Clearing site data or changing browsers may remove or hide it. This is not encrypted backup and must not be used for sensitive information.

### Rendering model

The app uses plain JavaScript and template-string rendering rather than a component framework. `renderFeed`, `renderTodos`, and `renderNotes` render their respective content. `setView` switches the main workspace view. Event listeners are attached after each relevant render. Text inserted into HTML is escaped by `esc()`.

## 5. User flows

### 5.1 Capture a thought

1. Open Index feed.
2. Enter text in the Quick Capture field.
3. Press Enter or select Capture.
4. The app creates a new `note` feed entry.
5. The entry is persisted to browser local storage and appears at the top of the feed.

### 5.2 Simulate a voice recording

1. Select the small waveform button beside the capture field.
2. The Voice Capture dialog opens.
3. Enter a transcript in the text area.
4. Select Add to feed.
5. A new local feed item appears.

The dialog is a deliberate simulation. It does not request microphone permission, record audio, or call speech recognition.

### 5.3 Inspect a feed item

1. Select any feed row.
2. The detail dialog displays title, date/time, type, body, and the simulated action result.
3. Close the dialog using the × control or dialog dismissal.

### 5.4 Search and filter

- Search checks title, body, and action summary.
- Type filter narrows the list to Notes, Reminders, or Answers.
- Search and filter can be combined.
- Empty states are shown when there are no matches.

### 5.5 Manage todos

1. Select Todos in the sidebar.
2. Add a reminder using the input and Add reminder.
3. Toggle a checkbox to mark an item complete.
4. Changes are saved locally.

### 5.6 Manage note lists

1. Select Notes.
2. Browse the seeded list cards.
3. Select New note list.
4. Enter a list name in the browser prompt.
5. The new list is saved locally.

### 5.7 Export

Select the ↗ control in the top bar. The browser downloads `index-demo-export.json`, containing the export timestamp and current entries, todos, and note lists.

## 6. Setup

### Requirements

- Node.js 20 or later recommended.
- npm 10 or later recommended.
- A modern browser (current Chrome, Edge, Firefox, or Safari).
- Internet access only for Google Fonts; the app itself has no runtime API dependency.

### Install

```bash
npm install
```

### Run the development server

```bash
npm run dev
```

Vite prints a local URL, normally `http://localhost:5173`. Open it in a browser.

### Production build

```bash
npm run build
```

The static production output is written to `dist/`.

### Preview the production build

```bash
npm run preview
```

## 7. Project tree

```text
pebble-index-web/
├── index.html
├── package.json
├── README.md
├── docs/
│   └── RESEARCH-NOTES.md
└── src/
    ├── main.js
    └── style.css
```

## 8. Browser compatibility and limitations

This project targets standard desktop and mobile browsers. It does not currently use the Web Bluetooth API. Even where Web Bluetooth is available, a browser implementation would require the actual device's advertised services, characteristics, permissions, protocol framing, and a secure context. The public developer guide describes the mobile app's role and ring behavior, but this project does not invent undocumented BLE UUIDs or wire formats.

A web app also cannot silently reproduce native background execution, iOS/Android notification access, persistent BLE reconnection, native local speech models, or platform integrations. These require native app capabilities, backend services, explicit permissions, or a separately engineered device integration.

## 9. Security and privacy

- No account sign-in exists.
- No backend or telemetry endpoint is configured.
- No external API calls are made by application code.
- Demo content is stored in local browser storage in plaintext.
- Do not enter confidential, regulated, or highly sensitive information.
- Exported JSON is also plaintext; store it accordingly.
- The Google Fonts stylesheet is an external font resource. Remove its `<link>` tags for a fully offline visual build and use system fonts instead.

## 10. Verification checklist

After starting the app, verify:

- [ ] Feed initially displays seeded entries.
- [ ] Selecting a feed row opens the detail dialog.
- [ ] Text capture adds an entry at the top.
- [ ] Voice dialog accepts text and adds an entry.
- [ ] Search narrows the feed.
- [ ] Type filter narrows the feed.
- [ ] Todos view allows adding and completing items.
- [ ] Notes view renders lists and allows creating a list.
- [ ] Settings view renders its preference cards.
- [ ] Export downloads valid JSON.
- [ ] Refresh preserves entries, todos, and note lists.
- [ ] Layout remains usable at narrow mobile widths.

## 11. Extension roadmap

Potential next steps, clearly separated from the current prototype:

1. **Componentize the UI:** migrate to React, Vue, or Svelte if the application grows.
2. **Add typed models:** introduce TypeScript interfaces and schema validation.
3. **Add automated tests:** unit tests for filters, serialization, and capture; browser tests for navigation and dialogs.
4. **Add IndexedDB:** use a structured local database for larger recordings and metadata.
5. **Add audio import:** allow users to import a local audio file, with a clearly disclosed transcription provider.
6. **Add a backend adapter:** define a service boundary for notes, tasks, and transcription rather than embedding provider logic in UI components.
7. **Add integrations:** implement webhook/MCP destinations only with explicit configuration, secure secret handling, and clear consent.
8. **Explore device connectivity:** only after consulting the public app implementation and validating actual hardware behavior. Do not guess BLE service identifiers or command payloads.
9. **Accessibility:** keyboard focus states, screen-reader labels, reduced-motion preferences, and contrast review.
10. **Visual QA:** compare against current public screenshots and user-provided captures, not assumptions about private screens.

## 12. Reverse-engineering methodology

This is a black-box UI study using public product documentation and observable workflows. The work is divided into:

1. **Product decomposition:** identify the ring's job and the companion app's job.
2. **Information architecture:** map documented Index Feed, Recording Details, Todos, Notes, capture input, and settings.
3. **Interaction reconstruction:** implement representative flows with deterministic local state.
4. **Evidence separation:** label mock behavior and avoid representing unimplemented features as functional.
5. **Validation:** test the app's actual browser interactions and persistence.

No proprietary binaries were decompiled, no private APIs were accessed, and no undocumented hardware protocol is claimed.

## 13. License and attribution

This project is an independent implementation for research and prototyping. It does not include Pebble source code, firmware, trademarks as product branding beyond nominative identification, or proprietary artwork. The product name is used only to identify the compatibility/research target. Review the official repository's license before reusing any upstream code: <https://github.com/coredevices/mobileapp>.

## 14. Known limitations

- Seed dates and times are illustrative static demo content.
- No true chronological date grouping is implemented.
- Note-list counts are sample metadata and do not automatically reconcile with feed entries.
- Settings controls are illustrative and are not persisted or connected to a service.
- Todo items are separate from feed reminders.
- Voice input is transcript text simulation only.
- No audio waveform, audio player, original recording, or device status API is present.
- No server-side synchronization or multi-user model exists.

## 15. Changelog

### 1.0.0

- Initial web UI reconstruction.
- Index feed, detail dialog, quick text capture, voice simulation, search/filter, Todos, Notes, settings, local persistence, and JSON export.
