# Architecture and Data Schema Design

## System Components

1. **Mobile Frontend**  
   - Collects user preferences (budget, dates, location, style).  
   - Renders itineraries and cached prices.  
   - Optional Live Price toggle for paid users.

2. **Backend API Server**  
   - **Endpoints**  
     - `POST /plan-trip`: forwards prefs to Orchestrator, returns `tripId` + initial itinerary with cached prices.  
     - `GET /trip/{tripId}`: returns saved itinerary and cached prices.  
     - `GET /trip/{tripId}/prices?live=true&interval={...}`: fetches fresh prices for each span, updates cache, returns new prices.  
   - **Cache Layer**  
     - Key: `tripId + spanId`  
     - Value: last price + timestamp  
     - TTL: a few hours  
   - **Persistence**  
     - Stores itineraries, span metadata, and cache entries.  
     - Tracks user settings (livePriceEnabled, interval).

3. **Local Orchestrator Service**  
   - Hosts local LLM for orchestration.  
   - Steps:  
     1. Send user prefs to Cloud LLM → structured plan.  
     2. Parse and rank itinerary options. (with local models) 
     3. Compose and test one-off API call per booking span; assign `spanId`.  
     4. Fetch initial price, return spans + prices to Backend.

4. **Cloud LLM Service**  
   - Performs travel planning with web search.  
   - Returns structured JSON of tripOptions with `bookingNeeded` spans.

5. **External Booking APIs (e.g. Agoda)**  
   - Queried one-off via Backend or orchestrator test calls.  
   - No direct frontend access.

---

## MongoDB Schemas

### 1. Users
\`\`\`js
{
  _id: ObjectId,
  email: String,            // unique, indexed
  name: String,
  passwordHash: String,
  createdAt: Date,
  updatedAt: Date,
  settings: {
    livePriceEnabled: Boolean,
    livePriceInterval: String
  },
  subscription: {
    tier: String,
    validUntil: Date
  }
}
\`\`\`

### 2. Trips
\`\`\`js
{
  _id: ObjectId,
  userId: ObjectId,         // ref → Users._id
  createdAt: Date,
  updatedAt: Date,
  status: String,           // e.g. "draft", "saved", "booked"
  title: String,
  spans: [ ObjectId ],      // array of TripSpan._id
  metadata: {
    budget: Number,
    startDate: Date,
    endDate: Date,
    location: String,
    style: String
  }
}
\`\`\`

### 3. TripSpans
\`\`\`js
{
  _id: ObjectId,
  tripId: ObjectId,         // ref → Trips._id
  spanId: String,           // unique within trip
  service: String,          // "hotel", "flight", "train"
  details: {
    location?: String,
    checkin?: String,
    checkout?: String,
    date?: String,
    route?: String,
    passengers?: Number
  },
  apiSpec: {
    method: String,
    url: String,
    headers?: Object,
    queryParams?: Object,
    body?: Object
  },
  price: Number,
  currency: String,
  fetchedAt: Date
}
\`\`\`

---

## Orchestrator → Backend Payload Schema

\`\`\`json
{
  "tripId": "648f1e9bcf1a5f0012ab3456",
  "spans": [
    {
      "spanId":  "hotel-1",
      "service": "hotel",
      "details": {
        "location": "Bergen",
        "checkin":  "2025-07-01",
        "checkout": "2025-07-03",
        "guests":   2
      },
      "apiSpec": {
        "method": "GET",
        "url":    "https://api.agoda.com/v1/hotels/search",
        "queryParams": {
          "location": "Bergen",
          "checkin":  "2025-07-01",
          "checkout": "2025-07-03",
          "guests":   "2"
        }
      },
      "price":    150.00,
      "currency": "USD",
      "fetchedAt":"2025-06-13T08:30:00Z"
    }
  ]
}
\`\`\`

---

## LLM Prompt Template

\`\`\`txt
You are a trip-planning assistant.
Return a JSON object exactly matching this schema:

{
  "tripOptions": [
    {
      "days": [
        {
          "date": "YYYY-MM-DD",
          "activities": [
            {
              "time": "HH:MM",
              "description": "string"
            }
          ]
        }
      ],
      "bookingNeeded": [
        {
          "spanId":  "string",
          "service": "hotel"|"flight"|"train"|"car",
          "details": {
            "location": "string",
            "checkin":  "YYYY-MM-DD",
            "checkout": "YYYY-MM-DD",
            "guests":   Number,
            "route":    "string",
            "date":     "YYYY-MM-DD",
            "class"?:   "string"
          }
        }
      ]
    }
  ]
}

### User Preferences
- budget: {{budget}}
- startDate: {{startDate}}
- endDate:   {{endDate}}
- location:  "{{location}}"
- style:     "{{style}}"

#### Instructions:
1. Output pure JSON only, no prose.
2. Use exactly the keys above.
3. Ensure each spanId is unique.
\`\`\`
