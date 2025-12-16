"""Deterministic CLI helper for managing tasks in a Notion database."""

import argparse
import os
from datetime import date
from typing import Any, Dict, Iterable, List, Optional

import requests

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def require_env() -> Dict[str, str]:
    token = os.getenv("NOTION_API_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")
    if not token or not database_id:
        raise EnvironmentError("NOTION_API_TOKEN and NOTION_DATABASE_ID must be set.")
    return {"token": token, "database_id": database_id}


def notion_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def check_response(response: requests.Response) -> None:
    if response.ok:
        return
    try:
        details = response.json()
    except ValueError:
        details = response.text
    raise RuntimeError(f"Notion API error {response.status_code}: {details}")


def format_rich_text(text: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    if not text:
        return None
    return [{"text": {"content": text}}]


def build_properties(
    title: Optional[str] = None,
    status: Optional[str] = None,
    due: Optional[str] = None,
    priority: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    properties: Dict[str, Any] = {}
    if title:
        properties["Name"] = {"title": [{"text": {"content": title}}]}
    if status:
        properties["Status"] = {"select": {"name": status}}
    if due:
        properties["Due"] = {"date": {"start": due}}
    if priority:
        properties["Priority"] = {"select": {"name": priority}}
    if notes:
        properties["Notes"] = {"rich_text": format_rich_text(notes)}
    return properties


def create_task(
    *,
    token: str,
    database_id: str,
    title: str,
    status: Optional[str],
    due: Optional[str],
    priority: Optional[str],
    notes: Optional[str],
) -> Dict[str, Any]:
    properties = build_properties(title=title, status=status, due=due, priority=priority, notes=notes)
    payload = {"parent": {"database_id": database_id}, "properties": properties}
    response = requests.post(
        f"{NOTION_API_BASE}/pages", headers=notion_headers(token), json=payload, timeout=30
    )
    check_response(response)
    return response.json()


def update_task(
    *,
    token: str,
    page_id: str,
    title: Optional[str],
    status: Optional[str],
    due: Optional[str],
    priority: Optional[str],
    notes: Optional[str],
) -> Dict[str, Any]:
    properties = build_properties(title=title, status=status, due=due, priority=priority, notes=notes)
    payload: Dict[str, Any] = {"properties": properties}
    response = requests.patch(
        f"{NOTION_API_BASE}/pages/{page_id}", headers=notion_headers(token), json=payload, timeout=30
    )
    check_response(response)
    return response.json()


def archive_task(*, token: str, page_id: str, archived: bool) -> Dict[str, Any]:
    payload = {"archived": archived}
    response = requests.patch(
        f"{NOTION_API_BASE}/pages/{page_id}", headers=notion_headers(token), json=payload, timeout=30
    )
    check_response(response)
    return response.json()


def list_tasks(
    *, token: str, database_id: str, status: Optional[str], page_size: int, start_cursor: Optional[str]
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"page_size": page_size}
    if status:
        payload["filter"] = {"property": "Status", "select": {"equals": status}}
    if start_cursor:
        payload["start_cursor"] = start_cursor
    response = requests.post(
        f"{NOTION_API_BASE}/databases/{database_id}/query",
        headers=notion_headers(token),
        json=payload,
        timeout=30,
    )
    check_response(response)
    return response.json()


def extract_title(page: Dict[str, Any]) -> str:
    title = page.get("properties", {}).get("Name", {}).get("title", [])
    if not title:
        return "(untitled)"
    return "".join(chunk.get("plain_text", "") for chunk in title)


def extract_select(page: Dict[str, Any], prop: str) -> Optional[str]:
    prop_data = page.get("properties", {}).get(prop)
    if not prop_data:
        return None
    selected = prop_data.get("select")
    if selected:
        return selected.get("name")
    return None


def extract_due(page: Dict[str, Any]) -> Optional[str]:
    due_data = page.get("properties", {}).get("Due", {}).get("date")
    if not due_data:
        return None
    return due_data.get("start")


def print_tasks(pages: Iterable[Dict[str, Any]]) -> None:
    for page in pages:
        title = extract_title(page)
        status = extract_select(page, "Status") or "(no status)"
        due = extract_due(page)
        page_id = page.get("id")
        line = f"{title} — {status} — {page_id}"
        if due:
            line = f"{line} — due {due}"
        print(line)


def parse_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    parsed = date.fromisoformat(value)
    return parsed.isoformat()


def cli(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Manage tasks in a Notion database deterministically.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--status", help="Filter by Status select value")
    list_parser.add_argument("--page-size", type=int, default=10, help="Number of tasks to fetch per request")
    list_parser.add_argument("--start-cursor", help="Pagination cursor from a previous run")

    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("--title", required=True, help="Task title")
    add_parser.add_argument("--status", help="Initial status")
    add_parser.add_argument("--due", help="Due date (YYYY-MM-DD)")
    add_parser.add_argument("--priority", help="Priority select value")
    add_parser.add_argument("--notes", help="Notes rich text content")

    update_parser = subparsers.add_parser("update", help="Update fields on an existing task")
    update_parser.add_argument("--page-id", required=True, help="Notion page ID to update")
    update_parser.add_argument("--title", help="New title")
    update_parser.add_argument("--status", help="New status")
    update_parser.add_argument("--due", help="New due date (YYYY-MM-DD)")
    update_parser.add_argument("--priority", help="New priority value")
    update_parser.add_argument("--notes", help="Notes rich text content")

    archive_parser = subparsers.add_parser("archive", help="Archive or unarchive a task")
    archive_parser.add_argument("--page-id", required=True, help="Notion page ID to update")
    archive_parser.add_argument("--unarchive", action="store_true", help="Unarchive instead of archive")

    args = parser.parse_args(argv)
    env = require_env()

    if args.command == "list":
        response = list_tasks(
            token=env["token"],
            database_id=env["database_id"],
            status=args.status,
            page_size=args.page_size,
            start_cursor=args.start_cursor,
        )
        print_tasks(response.get("results", []))
        next_cursor = response.get("next_cursor")
        if next_cursor:
            print(f"Next cursor: {next_cursor}")
    elif args.command == "add":
        due = parse_date(args.due)
        created = create_task(
            token=env["token"],
            database_id=env["database_id"],
            title=args.title,
            status=args.status,
            due=due,
            priority=args.priority,
            notes=args.notes,
        )
        print(f"Created task {created.get('id')} — {extract_title(created)}")
    elif args.command == "update":
        due = parse_date(args.due)
        updated = update_task(
            token=env["token"],
            page_id=args.page_id,
            title=args.title,
            status=args.status,
            due=due,
            priority=args.priority,
            notes=args.notes,
        )
        print(f"Updated task {updated.get('id')} — {extract_title(updated)}")
    elif args.command == "archive":
        updated = archive_task(token=env["token"], page_id=args.page_id, archived=not args.unarchive)
        action = "Unarchived" if args.unarchive else "Archived"
        print(f"{action} task {updated.get('id')} — {extract_title(updated)}")


if __name__ == "__main__":
    cli()
