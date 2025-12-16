# Notion Tasks Manager Directive

## Goal
Maintain and update a Notion database of tasks with deterministic scripts so task capture, triage, and status updates are reliable and repeatable.

## Inputs
- Environment variables:
  - `NOTION_API_TOKEN`: Integration secret with write access to the target database.
  - `NOTION_DATABASE_ID`: Target database for all task operations.
- Task details supplied via CLI flags (title, status, due date, priority, notes).

## Outputs
- Task pages created or updated inside the configured Notion database.
- Console summaries describing actions taken (created tasks, updated statuses, archived pages, listed items).

## Tools
- Execution script: `execution/notion_tasks.py`
- Temporary files: none (data flows directly between CLI and API). If you generate exports, store them under `.tmp/` and avoid committing them.

## Expected database schema
- Title property named **"Name"** (type: title).
- Select property named **"Status"** with values you want to track (e.g., "Inbox", "In Progress", "Done").
- Date property named **"Due"** (optional).
- Select property named **"Priority"** (optional).
- Rich text property named **"Notes"** (optional).

## Standard operations
1. **List tasks**
   - Use `python execution/notion_tasks.py list --status <STATUS>` to filter by status or omit `--status` for all.
   - Adjust `--page-size` if you need more results in a single call.
2. **Add a task**
   - Run `python execution/notion_tasks.py add --title "<Title>" [--status <STATUS>] [--due YYYY-MM-DD] [--priority <VALUE>] [--notes "<Details>"]`.
   - Use statuses/priority values that already exist in the database to avoid Notion validation errors.
3. **Update a task**
   - Run `python execution/notion_tasks.py update --page-id <PAGE_ID> [--title <Title>] [--status <STATUS>] [--due YYYY-MM-DD] [--priority <VALUE>] [--notes "<Details>"]`.
   - The command only updates the fields you provide.
4. **Archive a task**
   - Run `python execution/notion_tasks.py archive --page-id <PAGE_ID>` to archive.
   - Use `--unarchive` if you need to restore.

## Edge cases
- Missing or incorrect property names cause Notion to reject requests; align properties with the schema above.
- Notion enforces rate limits; if you hit them, pause and retry with smaller batches.
- Date formatting must be `YYYY-MM-DD`.

## Maintenance
- When you learn new constraints (e.g., additional properties, status values, or better batching strategies), update this directive and the execution script accordingly.
