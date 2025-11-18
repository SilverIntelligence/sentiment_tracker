# Reddit App Setup

## Overview

The Reddit App provides a user interface for viewing sentiment data directly within Reddit. It displays data from the API endpoints as custom tabs on your subreddit.

## Reddit App Structure

The app consists of multiple tabs:

1. **Home**: Current prices, sentiment, top posts
2. **Sentiment**: Detailed sentiment charts and metrics
3. **Posts**: Leaderboard of impactful posts
4. **Markets**: Price data and market context
5. **About**: Info and rules

## Creating the Reddit App

1. **Go to Reddit Apps**:
   - Visit https://www.reddit.com/prefs/apps
   - Click "create another app..."

2. **App Configuration**:
   - **Name**: Sentiment Tracker
   - **App Type**: Web app
   - **Description**: Real-time precious metals sentiment analysis
   - **About URL**: Link to your API docs
   - **Redirect URI**: Not needed for this use case

3. **Get Credentials**:
   - Note the **Client ID** (under app name)
   - Note the **Client Secret**

4. **Add to .env**:
```env
REDDIT_CLIENT_ID=<your-client-id>
REDDIT_CLIENT_SECRET=<your-client-secret>
```

## Reddit App Manifest

The Reddit App is configured via a manifest JSON file. Here's the basic structure:

```json
{
  "appId": "sentiment-tracker",
  "name": "Sentiment Tracker",
  "description": "Real-time precious metals sentiment analysis",
  "version": "1.0.0",
  "tabs": [
    {
      "id": "home",
      "title": "Home",
      "type": "webview",
      "url": "https://your-api.com/app/home"
    },
    {
      "id": "sentiment",
      "title": "Sentiment",
      "type": "webview",
      "url": "https://your-api.com/app/sentiment"
    },
    {
      "id": "posts",
      "title": "Posts",
      "type": "webview",
      "url": "https://your-api.com/app/posts"
    }
  ],
  "permissions": [
    "identity",
    "read"
  ]
}
```

## Building App Views

Each tab is a web page that consumes the API. Here's a simple example:

### Home Tab (HTML)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Sentiment Tracker - Home</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .price-card { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .sentiment-bar { height: 30px; background: #ddd; border-radius: 3px; overflow: hidden; }
        .bullish { background: #4caf50; }
        .bearish { background: #f44336; }
    </style>
</head>
<body>
    <h1>Precious Metals Sentiment</h1>

    <div id="summary">Loading...</div>

    <script>
        fetch('https://your-api.com/api/v1/summary')
            .then(r => r.json())
            .then(data => {
                const html = `
                    <div class="price-card">
                        <h2>Gold (XAUUSD)</h2>
                        <p>Price: $${data.prices.XAUUSD.price.toFixed(2)}</p>
                        <p>24h Change: ${data.prices.XAUUSD.change_24h.toFixed(2)}%</p>
                    </div>
                    <div class="price-card">
                        <h2>Silver (XAGUSD)</h2>
                        <p>Price: $${data.prices.XAGUSD.price.toFixed(2)}</p>
                        <p>24h Change: ${data.prices.XAGUSD.change_24h.toFixed(2)}%</p>
                    </div>
                `;
                document.getElementById('summary').innerHTML = html;
            });
    </script>
</body>
</html>
```

## Hosting App Views

You have several options:

### Option 1: GitHub Pages

1. Create `docs/` directory
2. Add HTML files for each tab
3. Enable GitHub Pages
4. Point Reddit App URLs to GitHub Pages

### Option 2: Same Server as API

Add static file routes to FastAPI:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/app", StaticFiles(directory="app_views", html=True), name="app")
```

### Option 3: Separate Frontend

Build a React/Vue app that consumes the API and deploy to Vercel/Netlify.

## Pinning the App

1. **Moderator Access**: You need mod permissions on the subreddit
2. **Add App**: Go to subreddit settings → Apps
3. **Install**: Add your Reddit App
4. **Configure**: Pin it to appear in sidebar or as tab

## Testing

1. **Local Testing**:
```bash
# Start API
uvicorn app.main:app --reload

# Test endpoints
curl http://localhost:8000/api/v1/summary
```

2. **Reddit App Sandbox**:
   - Use Reddit's developer tools
   - Test in a private/test subreddit first

## Example Tabs

### Sentiment Tab

Shows charts of sentiment over time:
- Line chart of sentiment scores
- Mention volume bars
- Bull/bear ratio pie chart

Use Chart.js or similar for visualizations.

### Posts Tab

Leaderboard of top posts:
- Post title and link
- Impact score
- Sentiment indicator
- Engagement metrics

### Markets Tab

Price data and context:
- Current prices for gold/silver/ETFs
- Price charts (use API data + charting library)
- Futures basis
- Volatility metrics

## Mobile Support

Ensure app views are mobile-responsive:
- Use responsive CSS (flexbox/grid)
- Test on mobile devices
- Consider touch-friendly UI elements

## Rate Limiting

Reddit App views will call your API:
- Implement caching (already done)
- Use appropriate cache TTLs
- Monitor API usage

## Analytics

Track app usage:
- Add Google Analytics to app views
- Log API calls from app
- Monitor user engagement

## Updates

To update the app:
1. Update manifest JSON
2. Update app view HTML/CSS/JS
3. Deploy changes
4. Notify users if needed
