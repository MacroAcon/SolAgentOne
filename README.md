# Vibe Dev Newsletter & Podcast Automation

An automated system for generating weekly newsletters and podcasts focused on MCP updates and AI development news.

## Configuration

### RSS Feed Sources

The system uses a configuration file to manage RSS feed sources. You can add or remove sources by editing `config/sources.json`:

```json
{
  "rss_feeds": [
    "https://github.com/modelcontextprotocol/mcp-spec/releases.atom",
    "https://github.com/modelcontextprotocol/mcp-go/releases.atom",
    "https://openai.com/blog/rss.xml",
    "http://feeds.arstechnica.com/arstechnica/index",
    "https://www.anthropic.com/blog/rss.xml",
    "https://blog.google/technology/ai/rss/",
    "https://www.microsoft.com/en-us/ai/blog/rss",
    "https://aws.amazon.com/blogs/machine-learning/feed/"
  ]
}
```

To add a new source:
1. Find the RSS feed URL for the source you want to add
2. Add the URL to the `rss_feeds` array in `config/sources.json`
3. The scraper will automatically include the new source in its next run

To remove a source:
1. Simply delete the corresponding URL from the `rss_feeds` array
2. The scraper will no longer fetch content from that source

Note: The scraper implements deduplication to prevent duplicate content across feeds, so you can safely add multiple sources that might cover similar topics.

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
SERPAPI_KEY=your_serpapi_key
SLACK_WEBHOOK_URL=your_slack_webhook_url
IMGUR_CLIENT_ID=your_imgur_client_id

### AI Model Configuration (Optional)

You can optionally override the default AI models used for various tasks. If these are not set, the system will use sensible defaults (e.g., gpt-4, dall-e-3).

MODEL_ANALYST=gpt-4-turbo
MODEL_RESEARCHER=gpt-4
MODEL_SYNTHESIS=gpt-4-turbo
MODEL_SCRIPTWRITER=gpt-4
MODEL_NEWSLETTER=gpt-4
MODEL_QUALITY=gpt-4-turbo
MODEL_IMAGE=dall-e-3
MODEL_TTS=eleven_monolingual_v1
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables
4. Run the orchestrator:
   ```bash
   python orchestrator.py
   ```

## Weekly Workflow

The system runs automatically every Tuesday at 9 AM and performs the following tasks:

1. Scrapes news from configured RSS feeds
2. Generates weekly content (tool spotlight, privacy insight, community corner)
3. Creates podcast script and show notes
4. Generates newsletter header image
5. Produces newsletter content
6. Uploads podcast to Spotify for Podcasters
7. Schedules newsletter delivery via Mailchimp

## Directory Structure

```
.
├── config/
│   └── sources.json      # RSS feed configuration
├── data/
│   ├── episode_counter.txt
│   ├── latest_mcp_news.json
│   └── last_run.txt
├── history/
│   └── transcripts/      # Archived episode scripts
├── output/
│   ├── episode_script.txt
│   ├── show_notes.md
│   └── newsletter_draft.html
├── .env                  # Environment variables
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Contributing

Feel free to submit issues and enhancement requests! 