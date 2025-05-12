# Debug State – End of Session (Cleanup & Persistent Vite Errors)

## Current Status
- Major frontend cleanup completed: legacy files, unused pages, and old API layers removed.
- All required files for the current app structure are present and correctly named.
- All import paths are correct and case-sensitive.
- Download CSV features are working on all analytics pages.
- Routing and tab logic for analytics/overview are fixed and robust.

## Outstanding Issues
- Persistent "disallowed MIME type" and "NS_ERROR_CORRUPTED_CONTENT" errors in Vite dev server, despite:
  - Deleting `.vite` and `node_modules/.vite` cache folders
  - Reinstalling dependencies
  - Verifying all files and imports
  - Restarting the dev server and hard-refreshing the browser
- Errors affect both app code and some node_modules (e.g., `recharts`, `file-saver`, `@fortawesome`).

## Next Steps (for next session)
- Consider a full `node_modules` wipe and reinstall if not already done.
- Try a different browser or incognito mode to rule out browser cache.
- Review `vite.config.js` for any custom settings that could affect MIME types or file serving.
- If issues persist, consider cloning a fresh copy of the repo and copying over only the current `src` and config files.

**Stopping for the night. Ready to resume cleanup and debugging next session!** 