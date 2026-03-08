# talk-to-your-slackbot

Pickleball match review Slackbot. See PROJECT_CONTEXT.md for scope and architecture.

## Connecting Slack so messages reach the app

Typing in the channel alone does **not** send data to this app. Use one of these:

1. **Slash command** — In your Slack app, create a Slash Command and set its Request URL to `https://YOUR_PUBLIC_HOST/slack/command` (use [ngrok](https://ngrok.com) for local dev). In Slack, run e.g. `/coach why did player 1 and player 2 lose?`.

2. **@mention** — Enable Event Subscriptions, set Request URL to `https://YOUR_PUBLIC_HOST/slack/events`, subscribe to **app_mention**, add scope `app_mentions:read`. Then in a channel where the app is added, @mention the bot (e.g. `@Demo_Pickleball_Coach why did player 1 and player 2 lose?`).

Ensure the server is reachable from the internet (Slack cannot POST to `localhost`).
