# FIN Logger Releases

Public release channel for FIN Logger.

This repository intentionally contains **no application source code**. It hosts only:

- signed APK releases;
- `latest.json` used by the in-app updater;
- a GitHub Actions based Telegram bot.

The Android application checks `latest.json` directly from GitHub and downloads APK files from GitHub Releases.

## Telegram bot

The bot is polled by GitHub Actions every 5 minutes, so no VPS, Render, Cloudflare Worker or paid server is required.

Repository secrets:

- `TELEGRAM_BOT_TOKEN`
- `ADMIN_CHAT_ID`

Commands: `/start`, `/latest`, `/version`, `/bug`, `/idea`, `/myid`.
