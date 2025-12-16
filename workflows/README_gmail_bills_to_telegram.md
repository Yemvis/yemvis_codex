# Gmail → Bills → Telegram

This workflow watches a Gmail inbox for bill-like messages and pings you on Telegram with a quick summary plus a link back to the thread. It keeps a small dedupe cache so the same email is not processed twice.

## Files in this folder
- `gmail_bills_to_telegram.json` – importable n8n workflow
- `README_gmail_bills_to_telegram.md` – this setup guide

## Prerequisites
1. A self-hosted n8n instance (0.220+ recommended).
2. Gmail access with API enabled and an OAuth2 credential inside n8n (type **Gmail OAuth2 API**).
3. A Telegram bot token (create with [@BotFather](https://t.me/botfather)) and a chat ID to DM yourself.
4. The environment variables listed in `.env.example` added to the n8n host (or your preferred secrets store).
5. A Gmail label named **Bills/Auto** (create it once in Gmail or capture its ID via the Gmail node in n8n).

## Environment variables
Add the following to your n8n `.env` (or any secrets manager you use with credentials):

- `TELEGRAM_BOT_TOKEN` – used in the Telegram credential (paste into the credential UI using the expression editor `{{ $env.TELEGRAM_BOT_TOKEN }}`).
- `TELEGRAM_CHAT_ID` – numeric ID for the DM destination. To obtain it, send a message to your bot, then:
  - Ask [@get_id_bot](https://t.me/get_id_bot) or [@userinfobot](https://t.me/userinfobot), **or**
  - Call `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` once and read the `chat.id` field.
- Optional overrides:
  - `GMAIL_QUERY` – custom Gmail search (defaults to `in:inbox is:unread newer_than:7d`).
  - `BILL_KEYWORDS` – comma-separated keywords, e.g. `fatura,boleto,invoice,payment due`.
  - `ALLOWED_SENDERS` – comma-separated whitelist of full emails or domains (e.g. `contato@meubanco.com,utility.com.br`). When set, keyword matching is skipped and only this list is used.
  - `DRY_RUN` – set to `true` to log matches without hitting Telegram or labeling the email.
  - `BILLS_LABEL_ID` – optional Gmail label ID if you already know it (e.g. `Label_123456789`). Leave unset to rely on the label name `Bills/Auto`.

Restart n8n (or reload environment variables) after editing `.env` so the expressions resolve.

## Import & credential hookup
1. In n8n, go to **Workflows → Import from File** and choose `gmail_bills_to_telegram.json`.
2. Open the **Trigger: Gmail (new emails)** node and pick your Gmail OAuth2 credential.
3. Open the **Telegram: Send DM** node and select the Telegram credential that uses `{{ $env.TELEGRAM_BOT_TOKEN }}`.
4. Save the workflow and enable it once you finish testing.

## How to change the bill rules
- **Adjust keywords**: Set `BILL_KEYWORDS` in your `.env` to a comma list, e.g. `BILL_KEYWORDS=fatura,boleto,cartão,payment due`. Restart n8n so the Function node picks them up.
- **Whitelist senders**: Set `ALLOWED_SENDERS` to emails or domains (`bank@conta.com,@utility.com.br`) to only alert on those senders.
- **Fine-tune the Gmail search**: override `GMAIL_QUERY`, for example `GMAIL_QUERY=in:inbox newer_than:14d has:attachment`.
- **Dry run mode**: flip `DRY_RUN=true` to see matches in the execution log without contacting Telegram or adding the label.
- **Label behaviour**: create the Gmail label **Bills/Auto** manually (Settings → Labels → Create new). If you know the label ID, drop it into `BILLS_LABEL_ID` so the Gmail node uses it directly.

## Testing checklist
1. Temporarily set `GMAIL_QUERY=from:me subject:(test bill)` and send yourself an email with a subject/body containing one of the keywords or an allowed sender.
2. Enable `DRY_RUN=true` for the first run so you can inspect the execution without Telegram noise. Disable it afterwards to allow notifications.
3. Add one of your banks or utilities to `ALLOWED_SENDERS` (e.g. `ALLOWED_SENDERS=contas@meubanco.com.br`) to verify whitelist detection.
4. After import, run the workflow manually once from n8n to ensure the Gmail trigger, Function node, and Telegram node all resolve credentials correctly.
5. Confirm that the Gmail node can add the **Bills/Auto** label. If Gmail requires the label ID, fetch it with a temporary Gmail node (`Label → Get All`) and set `BILLS_LABEL_ID` accordingly.
6. When you are satisfied, revert `GMAIL_QUERY` to its default (or remove the env var) and set `DRY_RUN=false` before enabling the workflow.

## Maintenance tips
- The workflow keeps the last 500 processed Gmail message IDs in workflow static data to avoid duplicates. If you ever need to reprocess older mail, clear this cache via the n8n UI (Workflow → Settings → Reset workflow data).
- Keywords, sender lists, and queries are all environment driven, so you can adjust behaviour without editing the workflow itself.
- Telegram messages are plain text. Edit the **Telegram: Send DM** node if you prefer Markdown or want to include attachments.
