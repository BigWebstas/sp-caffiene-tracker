# Caffeine Tracker

A Super Productivity plugin that logs caffeine intake and simulates blood
caffeine level decay using a half-life model, and its effects on productivity throughout the day.

## Screenshots

<p>
  <img src="Images/desktop2.png" alt="Desktop view: gauge and quick add" width="49%" />
  <img src="Images/desktop1.png" alt="Desktop view: decay chart, log, and settings" width="49%" />
</p>
<p>
  <img src="Images/mobile.png" alt="Mobile view: gauge, quick add, and decay chart" width="31%" />
  <img src="Images/mobile_settings.png" alt="Mobile view: Settings &amp; drinks overlay" width="31%" />
  <img src="Images/mobile_reports.png" alt="Mobile view: Reports overlay with Caffeine impact charts" width="31%" />
</p>

## Features

- Sleep Streak shows consecutive days you stayed under your sleep threshold
- Reporting with export to mark down includes mermaid charts to show graphing data
- Quick-add buttons for common drinks (coffee, espresso, tea, energy drink,
  soda, pre-workout) plus a custom name/mg entry
- Live current caffeine level (mg), recomputed from every logged dose using
  `mg * 0.5^(hoursElapsed / halfLife)`
- Decay curve chart (past 4h to next 18h) with task burn down and habit tracking vs caffeine in your system
- Caffeine impact reports: task completions by caffeine level and by hour,
  estimate accuracy, most-worked tag by caffeine level, daily habit/time
  correlations, focus-session length, task creation rate, and caffeine by
  deadline proximity
- Adjustable half-life (default 5h, the commonly cited average) and
  threshold (default 50mg)
- Today's log with per-entry removal
- Data synced via `persistDataSynced` / `loadSyncedData`, so history follows
  you across devices
- Update check on open: a 🔔 button appears next to Reports when a newer
  GitHub release exists, linking straight to it

## Install

1. Grab a release zip
2. In Super Productivity: **Settings → Plugins → Upload Plugin**
3. Open it from the ☕ header button


## Notes

- The half-life model is a simplification for personal tracking, not medical
  advice — individual caffeine metabolism varies (genetics, pregnancy,
  medication, liver function).
- Entries older than 7 days are pruned automatically on load; the decay
  simulation only needs recent doses since older ones contribute a
  negligible amount at a 5h half-life.
- **Network access:** the only outbound call this plugin makes is a single
  read-only `GET` to `api.github.com/repos/BigWebstas/sp-caffiene-tracker/releases/latest`
  once per open, to check for a newer version. Nothing is sent besides the
  request itself — no telemetry, no data upload. This is what the `http`
  permission and `allowedHosts` entry in `manifest.json` are for.
- **Session-only data:** Super Productivity's plugin API doesn't expose *when*
  a habit was checked off or *when* you last switched tasks, only "what's
  true right now" for habits, or a live change event for the current task.
  The habit burndown line works around this by stamping each habit with the
  moment the plugin first sees it done, then remembering that stamp (it
  survives closing and reopening the plugin), so anything already done
  before you opened it today still lands at open-time rather than the real
  moment it happened. The focus-session-length chart has no such workaround:
  it only exists in memory while the plugin stays open and resets completely
  on every reopen. Everything else (caffeine log, tasks, estimate accuracy,
  hour-of-day, tag breakdown) uses real historical timestamps and isn't
  affected by either limitation.
