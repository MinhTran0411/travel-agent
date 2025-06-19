from typing import Dict, List, Optional
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.models.trip import TripPlan, TripPreferences, TripSpan, Transportation, Accommodation, Activity
from app.models.preferences import (
    PhysicalConstraint,
    LanguagePreference,
    TripPurpose,
    Interest,
    Pace
)
from app.services.preference_service import PreferenceService
from app.services.activity_processing_service import ActivityProcessingService
import json
import os
from dotenv import load_dotenv

load_dotenv()

class TripService:
    """
    A service for creating detailed trip plans using GPT-4 knowledge.
    """
    
    def __init__(self):
        """Initialize the TripService with LLM, preference service, and activity processing."""
        self.llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "gpt-4"),
            temperature=0.7
        )
        
        self.preference_service = PreferenceService()
        self.activity_processor = ActivityProcessingService()

    def _validate_span(self, span: Dict[str, any]) -> bool:
        """Validate a single trip span against our schema requirements."""
        required_fields = ["spanId", "spanTitle", "spanDescription", "from_location", "to_location", "startDate", "endDate"]
        
        # Check required fields exist
        for field in required_fields:
            if field not in span:
                return False
        
        # Validate optional arrays exist (can be empty)
        array_fields = ["transportation", "accommodation", "activities"]
        for field in array_fields:
            if field not in span:
                span[field] = []  # Set default empty array
            elif not isinstance(span[field], list):
                return False
        
        # Validate transportation items
        for transport in span.get("transportation", []):
            if not self._validate_transportation(transport):
                return False
        
        # Validate accommodation items
        for accommodation in span.get("accommodation", []):
            if not self._validate_accommodation(accommodation):
                return False
        
        # Validate activity items
        for activity in span.get("activities", []):
            if not self._validate_activity(activity):
                return False
                
        return True
    
    def _validate_transportation(self, transport: Dict[str, any]) -> bool:
        """Validate transportation object."""
        required_fields = ["type", "departureLocation", "arrivalLocation", 
                          "departureTime", "arrivalTime", "service_class"]
        for field in required_fields:
            if field not in transport:
                return False
        
        valid_types = ["train", "flight", "car", "bus", "ferry", "walk", "bicycle"]
        if transport["type"] not in valid_types:
            return False
        
        valid_classes = ["economy", "business", "first", "sleeper", "premium"]
        if transport["service_class"] not in valid_classes:
            return False
        
        return True
    
    def _validate_accommodation(self, accommodation: Dict[str, any]) -> bool:
        """Validate accommodation object."""
        required_fields = ["type", "location", "checkin", "checkout"]
        for field in required_fields:
            if field not in accommodation:
                return False
        
        valid_types = ["hotel", "resort", "airbnb", "hostel", "guesthouse"]
        if accommodation["type"] not in valid_types:
            return False
        
        return True
    
    def _validate_activity(self, activity: Dict[str, any]) -> bool:
        """Validate activity object."""
        required_fields = ["name", "description", "location", "startTime", "endTime"]
        for field in required_fields:
            if field not in activity:
                return False
        
        return True

    def _extract_json_from_response(self, response: str) -> Dict:
        """Extract and parse JSON from LLM response string."""
        try:
            # Clean and extract JSON from response
            response = response.strip()
            
            if not response:
                raise ValueError("Empty response from LLM")
            
            # Look for JSON blocks in markdown format
            if "```json" in response:
                start_idx = response.find("```json") + 7
                end_idx = response.find("```", start_idx)
                if end_idx != -1:
                    json_str = response[start_idx:end_idx].strip()
                else:
                    json_str = response[start_idx:].strip()
            else:
                # Extract JSON from response if it contains additional text
                start_idx = response.find('{')
                end_idx = response.rfind('}')
                if start_idx == -1 or end_idx == -1:
                    raise ValueError("No JSON object found in response")
                json_str = response[start_idx:end_idx + 1]
            
            # Clean up common JSON issues
            json_str = json_str.strip()
            
            if not json_str:
                raise ValueError("Empty JSON string after extraction")
            
            # Check if JSON appears to be truncated (missing closing brace)
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            
            if open_braces > close_braces:
                print(f"WARNING: JSON appears truncated. Open braces: {open_braces}, Close braces: {close_braces}")
                # Try to balance braces by adding closing braces
                missing_braces = open_braces - close_braces
                json_str += '}' * missing_braces
                print(f"Added {missing_braces} closing braces to balance JSON")
            
            # Log the complete JSON for debugging
            print(f"Parsing JSON (length: {len(json_str)} chars)")
            print("Complete JSON response:")
            print(json_str)
            
            # Parse JSON response
            data = json.loads(json_str)
            
            if not isinstance(data, dict):
                raise ValueError("Parsed JSON is not a dictionary")
            
            return data
            
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print(f"Error at position {e.pos}")
            if 'json_str' in locals():
                print(f"JSON content around error: {json_str[max(0, e.pos-50):e.pos+50]}")
            raise ValueError(f"Invalid JSON response from LLM: {e}. Check logs for details.")
        except Exception as e:
            print(f"Parse error: {str(e)}")
            print(f"Response content: {response}")
            raise ValueError(f"Failed to parse LLM response: {str(e)}")

    def _parse_llm_response_from_json(self, data: Dict) -> TripPlan:
        """Convert processed JSON dict to TripPlan object."""
        try:
            # Validate basic structure
            required_fields = ["tripId", "from_location", "to_location", "startDate", "endDate", "spans"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate each span
            for span in data["spans"]:
                if not self._validate_span(span):
                    raise ValueError(f"Invalid span structure: {span}")
            
            # Convert to TripPlan object
            trip_spans = []
            for span_data in data["spans"]:
                # Parse transportation
                transportation = []
                for transport_data in span_data.get("transportation", []):
                    transport = Transportation(
                        type=transport_data["type"],
                        provider=transport_data.get("provider"),
                        departureLocation=transport_data["departureLocation"],
                        arrivalLocation=transport_data["arrivalLocation"],
                        departureTime=datetime.fromisoformat(transport_data["departureTime"].replace('Z', '+00:00')),
                        arrivalTime=datetime.fromisoformat(transport_data["arrivalTime"].replace('Z', '+00:00')),
                        service_class=transport_data["service_class"],
                        passengers=int(transport_data.get("passengers", 1))
                    )
                    transportation.append(transport)
                
                # Parse accommodation
                accommodation = []
                for acc_data in span_data.get("accommodation", []):
                    acc = Accommodation(
                        type=acc_data["type"],
                        location=acc_data["location"],
                        checkin=datetime.fromisoformat(acc_data["checkin"].replace('Z', '+00:00')),
                        checkout=datetime.fromisoformat(acc_data["checkout"].replace('Z', '+00:00')),
                        guests=int(acc_data.get("guests", 1))
                    )
                    accommodation.append(acc)
                
                # Parse activities (now with activityId from processing)
                activities = []
                for activity_data in span_data.get("activities", []):
                    activity = Activity(
                        name=activity_data["name"],
                        description=activity_data["description"],
                        location=activity_data["location"],
                        startTime=datetime.fromisoformat(activity_data["startTime"].replace('Z', '+00:00')),
                        endTime=datetime.fromisoformat(activity_data["endTime"].replace('Z', '+00:00')),
                        participants=int(activity_data.get("participants", 1)),
                        category=activity_data.get("category", "general"),
                        activityId=activity_data.get("activityId")  # Include processed activity ID
                    )
                    activities.append(activity)
                
                # Create trip span
                trip_span = TripSpan(
                    spanId=span_data["spanId"],
                    spanTitle=span_data["spanTitle"],
                    spanDescription=span_data["spanDescription"],
                    from_location=span_data["from_location"],
                    to_location=span_data["to_location"],
                    startDate=datetime.fromisoformat(span_data["startDate"].replace('Z', '+00:00')),
                    endDate=datetime.fromisoformat(span_data["endDate"].replace('Z', '+00:00')),
                    transportation=transportation,
                    accommodation=accommodation,
                    activities=activities,
                    notes=span_data.get("notes")
                )
                trip_spans.append(trip_span)
            
            trip_plan = TripPlan(
                tripId=data["tripId"],
                title=data.get("title"),
                from_location=data["from_location"],
                to_location=data["to_location"],
                startDate=datetime.fromisoformat(data["startDate"].replace('Z', '+00:00')),
                endDate=datetime.fromisoformat(data["endDate"].replace('Z', '+00:00')),
                spans=trip_spans
            )
            
            return trip_plan
            
        except Exception as e:
            print(f"Parse error: {str(e)}")
            raise ValueError(f"Failed to convert JSON to TripPlan: {str(e)}")

    async def plan_trip(self, preferences: TripPreferences) -> TripPlan:
        """
        Create a detailed trip plan based on user preferences using LLM knowledge.
        
        Args:
            preferences: TripPreferences object containing all user preferences
            
        Returns:
            TripPlan: A validated trip plan object
            
        Raises:
            Exception: If trip planning fails
        """
        try:
            # Get preference details
            constraint_details = [
                self.preference_service.get_constraint_details(c) 
                for c in preferences.physical_constraints
            ]
            language_preference_details = self.preference_service.get_language_preference_details(
                preferences.language_preference
            )
            trip_purpose_details = self.preference_service.get_trip_purpose_details(
                preferences.trip_purpose
            )
            pace_details = self.preference_service.get_pace_details(preferences.pace)
            interest_details = [
                self.preference_service.get_interest_details(i) 
                for i in preferences.interests
            ]

            # Create concise prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a travel agent. Create a detailed trip plan in JSON format.

CRITICAL: FILL THE ENTIRE TRIP DURATION with activities. Calculate the total days from start_date to end_date and create activities for EVERY SINGLE DAY of the trip. Do not leave any days empty.

RETURN TRIP RULE - READ CAREFULLY:
1. The LAST span MUST include return transportation to the original departure location
2. Example structure for last span:
   {{
     "spanId": "span_N",
     "spanTitle": "Return to {from_location}",
     "spanDescription": "Final day and return journey",
     "from_location": "Last city code",
     "to_location": "{from_location}",  // MUST match original departure location
     "transportation": [{{
       "type": "flight|train",
       "departureLocation": "Last city code",
       "arrivalLocation": "{from_location}",  // MUST match original departure location
       "departureTime": "Last day time",
       "arrivalTime": "Return time",
       "service_class": "economy|business|first"
     }}],
     "activities": [
       // Morning activities before departure
       // NO activities after departure time
     ]
   }}
3. The return trip MUST be on the last day (endDate)
4. Activities on the last day must end before the departure time
5. The to_location in the last span MUST match the original from_location

LOCATION NAMING RULES - READ CAREFULLY:
1. Use IATA airport codes for cities (e.g., "SIN" for Singapore, "TYO" for Tokyo)
2. Use ISO 3166-1 alpha-2 country codes (e.g., "JP" for Japan, "SG" for Singapore)
3. Examples:
   - City: "SIN" (not "Singapore")
   - Country: "JP" (not "Japan")
   - City: "TYO" (not "Tokyo")
   - Country: "TH" (not "Thailand")
4. For multi-city trips, use the appropriate IATA code for each city
5. For activities within a city, use the IATA code in the location field

BUDGET PRIORITY: Use ${budget} to select accommodation types (budget: hostel/guesthouse, mid-range: hotel, luxury: resort) and activities.

ACTIVITY NAMING RULES - READ CAREFULLY:
1. Use ONLY standardized, commonly recognized names for activities
2. DO NOT include dates or times in activity names
3. Use the most concise, official name that tourists would recognize
4. Examples of good names:
   - "Tokyo Skytree" (not "Day 1: Morning - Tokyo Skytree Observation Deck")
   - "Senso-ji Temple" (not "Day 2: Afternoon - Ancient Buddhist Temple Visit")
   - "Tsukiji Outer Market" (not "Day 3: Morning - Local Fish Market Tour")
5. Avoid descriptive phrases in names - put those in the description field instead

TRIP SCOPE RULES:
- If fix_city=true: Stay within the specified destination_city, create multiple activities exploring different districts/areas
- If fix_country=true: Visit multiple cities within the destination_country, create spans for different cities
- If both false: Multi-country trip starting from destination

JSON STRUCTURE:
{{
    "tripId": "trip_12345",
    "title": "Trip Title",
    "from_location": "{from_location}",
    "to_location": "{from_location}",
    "startDate": "{start_date}",
    "endDate": "{end_date}",
    "spans": [{{
        "spanId": "span_1",
        "spanTitle": "Span Title",
        "spanDescription": "Description",
        "from_location": "Origin",
        "to_location": "Destination",
        "startDate": "2024-01-01",
        "endDate": "2024-01-03",
        "transportation": [{{
            "type": "flight|train|car|bus",
            "provider": "Provider",
            "departureLocation": "SIN",
            "arrivalLocation": "TYO",
            "departureTime": "2024-01-01T10:00:00Z",
            "arrivalTime": "2024-01-01T14:00:00Z",
            "service_class": "economy|business|first",
            "passengers": 1
        }}],
        "accommodation": [{{
            "type": "hotel|hostel|guesthouse|airbnb",
            "location": "TYO",
            "checkin": "2024-01-01T15:00:00Z",
            "checkout": "2024-01-03T11:00:00Z",
            "guests": 1
        }}],
        "activities": [{{
            "name": "Activity Name",
            "description": "Description",
            "location": "TYO",
            "startTime": "2024-01-01T09:00:00Z",
            "endTime": "2024-01-01T12:00:00Z",
            "participants": 1,
            "category": "museum|tour|food|shopping|general"
        }}, {{
            "name": "Activity Name",
            "description": "Description", 
            "location": "TYO",
            "startTime": "2024-01-02T09:00:00Z",
            "endTime": "2024-01-02T12:00:00Z",
            "participants": 1,
            "category": "museum|tour|food|shopping|general"
        }}],
        "notes": "Notes"
    }}]
}}

CRITICAL ACTIVITY REQUIREMENTS - READ CAREFULLY:
1. CALCULATE: Count days from {start_date} to {end_date} = {trip_duration_days} days
2. MANDATORY: Create activities for ALL {trip_duration_days} days
3. EXACT DATES TO FILL: {daily_dates}
4. For EACH date above, create 2-4 activities (morning, afternoon, evening)
5. Match activities to user interests: {interests}
6. Consider pace: {pace} (relaxed=fewer activities, fast=more activities)

EXAMPLE for 3-day trip (2025-01-01 to 2025-01-03):
"spans": [
  {{
    "spanId": "span_1",
    "spanTitle": "Tokyo Exploration",
    "from_location": "SIN",
    "to_location": "TYO",
    "transportation": [{{
      "type": "flight",
      "departureLocation": "SIN",
      "arrivalLocation": "TYO",
      "departureTime": "2025-01-01T08:00:00Z",
      "arrivalTime": "2025-01-01T16:00:00Z",
      "service_class": "economy"
    }}],
    "activities": [
      {{"name": "Tokyo Skytree", "location": "TYO", "startTime": "2025-01-01T17:00:00Z", ...}}
    ]
  }},
  {{
    "spanId": "span_2",
    "spanTitle": "Return to Singapore",
    "from_location": "TYO",
    "to_location": "SIN",
    "transportation": [{{
      "type": "flight",
      "departureLocation": "TYO",
      "arrivalLocation": "SIN",
      "departureTime": "2025-01-03T14:00:00Z",
      "arrivalTime": "2025-01-03T22:00:00Z",
      "service_class": "economy"
    }}],
    "activities": [
      {{"name": "Last Morning Activity", "location": "TYO", "startTime": "2025-01-03T09:00:00Z", "endTime": "2025-01-03T12:00:00Z", ...}}
    ]
  }}
]

FAILURE TO INCLUDE ALL DATES IS UNACCEPTABLE!

REQUIREMENTS:
- Return ONLY valid JSON
- Generate unique IDs (trip_XXXXX, span_XXXXX)
- Use budget-appropriate accommodation and activities
- Fill EVERY day from start_date to end_date with activities
- Use standardized, concise activity names without dates
- Use IATA codes for cities and ISO country codes
- ALWAYS include return trip in the last span
- No trailing commas or comments

WARNING: If you create fewer than {trip_duration_days} days worth of activities, your response will be REJECTED. Double-check that you have activities spanning from {start_date} to {end_date} before responding."""),
                ("user", """Plan a trip with these preferences:
                - From Location: {from_location} (use IATA code)
                - Destination: {destination} (use IATA code)
                - Trip Scope: {trip_scope}
                - Start Date: {start_date}
                - End Date: {end_date}
                - Budget: ${budget}
                - Physical Constraints: {physical_constraints}
                - Language Preference: {language_preference} ({language_preference_details})
                - Trip Purpose: {trip_purpose} ({trip_purpose_details})
                - Interests: {interests}
                - Pace: {pace} ({pace_details})
                - Additional Notes: {additional_notes}

TRIP SCOPE DETAILS:
- Fixed to city: {fix_city}
- Fixed to country: {fix_country}  
- Destination city: {destination_city} (use IATA code)
- Destination country: {destination_country} (use ISO code)

🚨 CRITICAL CHECKLIST - COMPLETE ALL STEPS:
□ STEP 1: This trip is {trip_duration_days} days long ({start_date} to {end_date})
□ STEP 2: These exact dates MUST have activities: {daily_dates}
□ STEP 3: Create 2-4 activities for each date above
□ STEP 4: Double-check you have activities for all {trip_duration_days} days
□ STEP 5: Verify no dates from {daily_dates} are missing
□ STEP 6: Verify all locations use IATA codes for cities and ISO codes for countries
□ STEP 7: Verify the last span includes return trip to {from_location}

DO NOT PROCEED until you confirm ALL dates have activities and ALL locations use proper codes!""")
            ])

            # Calculate trip duration and daily dates
            # For trip dates, we want to include both start and end dates
            trip_duration = (preferences.end_date.date() - preferences.start_date.date()).days + 1
            daily_dates = []
            current_date = preferences.start_date.date()
            end_date = preferences.end_date.date()
            while current_date <= end_date:
                daily_dates.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)
            
            print(f"DEBUG: Trip duration calculated as {trip_duration} days")
            print(f"DEBUG: Daily dates: {daily_dates}")

            # Prepare the input
            prompt_input = {
                "from_location": preferences.from_location,
                "destination": preferences.destination,
                "trip_scope": preferences.trip_scope_description,
                "start_date": preferences.start_date.isoformat(),
                "end_date": preferences.end_date.isoformat(),
                "budget": preferences.budget,
                "physical_constraints": [f"{c.value}: {detail}" for c, detail in zip(preferences.physical_constraints, constraint_details)],
                "language_preference": preferences.language_preference.value,
                "language_preference_details": language_preference_details,
                "trip_purpose": preferences.trip_purpose.value,
                "trip_purpose_details": trip_purpose_details,
                "interests": [f"{i.value}: {detail}" for i, detail in zip(preferences.interests, interest_details)],
                "pace": preferences.pace.value,
                "pace_details": pace_details,
                "additional_notes": preferences.additional_notes or "None",
                "fix_city": preferences.fix_city,
                "fix_country": preferences.fix_country,
                "destination_city": preferences.destination_city,
                "destination_country": preferences.destination_country,
                "trip_duration_days": trip_duration,
                "daily_dates": ", ".join(daily_dates)
            }

            # Generate the trip plan using the LLM
            chain = prompt | self.llm
            result = await chain.ainvoke(prompt_input)
            
            # Parse the raw LLM response to JSON
            raw_json = self._extract_json_from_response(result.content)
            
            # Process activities: normalize, deduplicate, assign IDs
            processed_json = self.activity_processor.process_trip_plan(raw_json)
            
            # Parse and validate the processed response
            trip_plan = self._parse_llm_response_from_json(processed_json)

            return trip_plan

        except Exception as e:
            raise Exception(f"Failed to plan trip: {str(e)}") 