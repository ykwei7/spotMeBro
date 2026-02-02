# Spot Me Bro – Telegram Gym Bot

A Telegram bot that helps you track lifts, set goals, and get AI-powered workout recommendations.

## Features

- **/setgoal** – Set or change your fitness goal anytime
- **/track** – Log lifts via free-form text (e.g. "Bench press 3x5 at 135 lbs"). If parsing misses data, the bot prompts you step-by-step, then asks for confirmation before saving
- **/recommend** – Get workout suggestions based on your history and goal. Add optional text to tailor (e.g. `/recommend leg day`)
- **/view** – See past lifts grouped by date

## Setup

### 1. Create a Telegram bot

1. Open [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the bot token

### 2. Get a Groq API key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up and create an API key

### 3. Set up Supabase

1. Go to [supabase.com](https://supabase.com) and create a project
2. In the SQL Editor, run the contents of `supabase/schema.sql`
3. In Project Settings → API, copy the **Project URL** and **service_role** key

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

- `TELEGRAM_BOT_TOKEN` – from BotFather
- `GROQ_API_KEY` – from Groq console
- `SUPABASE_URL` – your Supabase project URL
- `SUPABASE_SERVICE_KEY` – your Supabase service role key

### 5. Install and run

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python bot.py
```

## Project layout

```
spot-me-bro/
├── bot.py           # Main entry point
├── config.py        # Loads env vars
├── db.py            # Supabase / DB helpers
├── handlers.py      # Command and conversation handlers
├── llm.py           # Groq parsing and recommendations
├── requirements.txt
├── supabase/
│   └── schema.sql   # Table definitions
└── README.md
```
