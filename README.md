# yemvis_codex

CLI tooling plus directives for managing a Notion tasks database using a deterministic 3-layer workflow.

## Repository layout
- `AGENTS.md`: High-level agent guidance.
- `directives/`: SOPs describing goals, inputs, outputs, and edge cases.
- `execution/`: Deterministic scripts that implement the directives.
- `.tmp/`: Workspace for intermediate data (regenerated as needed).

## Prerequisites
- Python 3.10+
- Install dependencies: `pip install -r requirements.txt`
- Environment variables:
  - `NOTION_API_TOKEN`
  - `NOTION_DATABASE_ID`

## Usage
1. Review `directives/notion_tasks.md` for the expected Notion database schema and operating procedures.
2. Run commands from the repository root:
   - List tasks: `python execution/notion_tasks.py list --status Inbox`
   - Add a task: `python execution/notion_tasks.py add --title "Draft PR" --status "In Progress" --due 2024-06-30`
   - Update a task: `python execution/notion_tasks.py update --page-id <PAGE_ID> --status Done`
   - Archive a task: `python execution/notion_tasks.py archive --page-id <PAGE_ID>`

## Notes
- Keep `.tmp/` contents untracked; regenerate as needed.
- Update directives when you learn new constraints or optimizations for the Notion workflow.
