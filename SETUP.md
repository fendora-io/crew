# Setup

End-to-end deployment of `crew` on a fresh Ubuntu 24.04 server. ~20 minutes.

## 1. Accounts

### Anthropic API key
- [console.anthropic.com](https://console.anthropic.com) → API Keys → Create Key
- Add €10 of credit; daily use is ~€0.20-0.50
- **Set a hard monthly spend cap** (Settings → Billing → Limits). The default
  alerts won't stop a leaked key from billing you €1,000 overnight.
- Save as `ANTHROPIC_API_KEY`

### Telegram bot
1. On Telegram, DM `@BotFather`
2. Send `/newbot`, follow the prompts (name + username ending in `bot`)
3. Copy the token shown — save as `TELEGRAM_BOT_TOKEN`
4. **DM your new bot something** (any message, e.g. "hi"). Telegram won't let
   the bot message you first until you do this.
5. Get your chat ID: open in a browser:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
6. Find `"chat":{"id":NUMBER,...}` in the JSON — save `NUMBER` as `TELEGRAM_CHAT_ID`

### (Optional) NVD API key
- [request one here](https://nvd.nist.gov/developers/request-an-api-key)
- Free, increases rate limit. Not required for daily use.
- Save as `NVD_API_KEY`

## 2. Server prep

These commands assume you've SSH'd into a fresh Ubuntu 24.04 box as `root`.

```bash
# Create a non-root user for the bot
adduser bot
usermod -aG sudo bot

# Install Python + git
apt update && apt install -y python3-pip python3-venv git

# Switch to the bot user
su - bot
```

## 3. Clone and install

```bash
# As the bot user
cd /opt
sudo mkdir crew && sudo chown bot:bot crew
cd crew

git clone git@github.com:fendora-io/crew.git .
# (If the box doesn't have your SSH key on GitHub, use https:
#  git clone https://github.com/fendora-io/crew.git .)

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4. Configure

You have two ways to provide secrets — pick one.

### Option A: Infisical (recommended for production)

Store `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (and
optionally `TELEGRAM_THREAD_ID`, `NVD_API_KEY`) in an
[Infisical](https://infisical.com) project. crew pulls them at startup
via Universal Auth — no plaintext secrets on disk except the bootstrap
credentials.

1. In your Infisical project, add the secrets above as keys (with their
   values) for the `prod` environment, either at the root path `/` or
   inside a folder like `/crew` if you prefer to namespace them.
2. Project → **Access Control → Machine Identities → Create**.
   Give the identity **read-only** access to the `/crew` path on `prod`.
   Save the `Client ID` and `Client Secret`.
3. Find your **Project ID** in Project Settings.
4. On the server:
   ```bash
   cp .env.example .env
   nano .env
   chmod 600 .env
   ```
   Fill in only the Infisical block:
   ```bash
   export INFISICAL_HOST=https://eu.infisical.com    # or app.infisical.com (US)
   export INFISICAL_CLIENT_ID=<machine-identity-client-id>
   export INFISICAL_CLIENT_SECRET=<machine-identity-client-secret>
   export INFISICAL_PROJECT_ID=<project-id>
   export INFISICAL_ENV=prod
   export INFISICAL_SECRET_PATH=/    # or /crew if you namespaced under a folder
   export CREW_DB_PATH=/opt/crew/state.db
   export CREW_TG_STATE=/opt/crew/last_update.txt
   ```
   Leave `ANTHROPIC_API_KEY` etc. commented out — they come from Infisical.

### Option B: Plain env (simplest for local dev)

```bash
cp .env.example .env
nano .env
chmod 600 .env
```

Uncomment the secret values directly:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export TELEGRAM_BOT_TOKEN=1234567890:ABC...
export TELEGRAM_CHAT_ID=987654321
export CREW_DB_PATH=/opt/crew/state.db
# export NVD_API_KEY=...  # optional
```

Anything you set in `.env` always wins over Infisical, so you can use
Option A in prod and override a single key locally with Option B.

## 5. Test before scheduling

```bash
cd /opt/crew
. .env
./venv/bin/python crew.py
```

Within ~30 seconds your Telegram should receive: a header message, then for
each of up to 3 signals a header card + LinkedIn post + X thread tweets, each
in copy-pasteable code blocks.

**Troubleshooting:**

- *No messages:* check the `TELEGRAM_CHAT_ID` is your personal ID and you've
  DM'd the bot at least once.
- *401 / 403:* token typo, or you copy-pasted whitespace.
- *Module not found:* you didn't activate the venv. `. .env` doesn't activate
  the venv — run `source venv/bin/activate` first, or invoke
  `./venv/bin/python crew.py` directly.
- *Anthropic error:* check the model string in `crew.py` matches a current
  model at [docs.claude.com](https://docs.claude.com).

## 6. Cron

```bash
crontab -e
```

Add:

```cron
# 06:00 UTC = 07:00 CET (winter) / 08:00 CEST (summer)
0 6 * * * cd /opt/crew && . .env && ./venv/bin/python crew.py >> /var/log/crew.log 2>&1
```

Create the log file:

```bash
sudo touch /var/log/crew.log
sudo chown bot:bot /var/log/crew.log
```

Tomorrow at 07:00 (or whatever you set), your first digest arrives.

## 7. Hardening (do this once, takes 5 min)

```bash
# Auto-install security patches
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades

# Disable password SSH (only if you have key auth working — test in another
# terminal first!)
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl reload ssh

# Verify the bot user can't sudo without password unless you want that
sudo deluser bot sudo   # optional — removes sudo access from bot user
```

See [SECURITY.md](./SECURITY.md) for the full operational hardening guide.

## 8. Daily flow

```
☕  07:00  Phone dings
   Read 3 drafts
   Tap-and-hold code block → Copy
   Paste into LinkedIn or X app
   Edit one line so it sounds like you
   Post
   Reply `done 2` to the bot (optional)
```

5-10 minutes including the human bottleneck.

## 9. Tuning the voice

Open `crew.py`, find `VOICE_SYSTEM_PROMPT` near the top. This is the entire
product. After a week of posting:

1. Add any awkward words the bot keeps producing to `BANNED WORDS`.
2. If LinkedIn posts feel too long/short, adjust the `LENGTHS` rules.
3. After 2-3 weeks, paste 3-5 of your own best posts into the prompt as
   examples ("Examples of posts that work well: ..."). The quality jump from
   few-shot examples is bigger than from any model upgrade.

Commit your edits back to the repo. The prompt is the product.

## 10. Updating

```bash
cd /opt/crew
git pull
source venv/bin/activate
pip install -r requirements.txt
```

No service to restart — the next cron tick picks up changes.
