import { defineConfig } from "@trigger.dev/sdk/v3";

/**
 * Trigger.dev v3 configuration.
 *
 * To connect this project:
 * 1. Create a project at https://cloud.trigger.dev (or run `npx trigger.dev@latest init`).
 * 2. Set the project ref (e.g. `proj_xxxxxxxxxxxxxxxxxxxxxxxx`) either:
 *    - here, replacing the placeholder below, or
 *    - as the `TRIGGER_PROJECT_ID` environment variable (recommended — keeps the
 *      ref out of source control).
 */
export default defineConfig({
  project: process.env.TRIGGER_PROJECT_ID ?? "proj_replace_with_your_project_ref",

  // The `trigger/` directory is auto-detected by Trigger.dev, but we declare it
  // explicitly so the task discovery is unambiguous.
  dirs: ["./trigger"],

  // Safety cap: no task may run longer than 15 minutes.
  maxDuration: 900,
});