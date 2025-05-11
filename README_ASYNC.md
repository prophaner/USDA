# USDA Nutrition Proxy API with Rate Limiting

This is an enhanced version of the USDA Nutrition Proxy API that includes:

1. **Rate Limiting**: Limits API calls to USDA to 1,000 requests per hour per IP address
2. **Async Processing**: Uses async/await for better concurrency and performance
3. **Concurrent Recipe Calculation**: Fetches multiple ingredients in parallel

## Features

- **Rate Limiting**: Prevents exceeding USDA API limits
- **Async Processing**: Better performance for concurrent requests
- **Rate Limit Headers**: Includes headers to track usage
- **Rate Limit Status Endpoint**: Check your current rate limit status

## API Endpoints

### Health Check
```
GET /
```

### Search for Ingredients
```
GET /search?q=pineapple%20juice&limit=5
```

### Get Ingredient Details
```
GET /ingredient?q=Pineapple%20juice
GET /ingredient?fdc_id=168885
GET /ingredient?q=apple&amount=2&unit=cup
```

### Calculate Recipe Nutrition
```
POST /recipe
Content-Type: application/json

[
  {"q": "Pineapple juice, canned", "amount": 1, "unit": "cup"},
  {"q": "Apple, raw", "amount": 2, "unit": "medium"},
  {"q": "Banana, raw", "amount": 1, "unit": "medium"}
]
```

### Check Rate Limit Status
```
GET /rate-limit
```

## Rate Limiting Behavior

The rate limiter counts USDA API calls, not HTTP requests to your server. This means:

1. Each call to the USDA API (search or get food details) counts as one request against your limit
2. A single HTTP request to your server might make multiple USDA API calls (e.g., the recipe endpoint)
3. The rate limit is per IP address, so different clients have separate limits

### Rate Limit Headers

All responses include the following headers:

- `X-RateLimit-Limit`: Maximum requests per hour (1000)
- `X-RateLimit-Remaining`: Remaining requests in the current window
- `X-RateLimit-Reset`: Time in seconds until the rate limit resets

### Checking Your Rate Limit

You can check your current rate limit status without affecting your limit by calling:

```
GET /rate-limit
```

This endpoint returns your current usage and does not count against your limit.

## Running the Async Server

To use the async version with rate limiting:

```bash
# Install dependencies
pip install httpx

# Run the server
uvicorn server_async:app --reload
```

## Implementation Details

### Rate Limiting

The rate limiter uses a sliding window algorithm to track requests per IP address. This ensures that clients can't exceed 1,000 requests per hour to the USDA API.

### Async Processing

All API calls to USDA are made asynchronously using `httpx`, which allows for better concurrency and performance. The recipe endpoint fetches multiple ingredients in parallel.

### Caching

Ingredient details are cached to minimize API calls to USDA. The cache is limited to the size specified in the configuration.

## Error Handling

When rate limits are exceeded, the API returns a 429 Too Many Requests response with a helpful error message.

## Migrating from the Sync Version

If you're migrating from the synchronous version:

1. Use `server_async.py` instead of `server.py`
2. Make sure to install `httpx`: `pip install httpx`
3. No changes needed to your API calls - the endpoints remain the same