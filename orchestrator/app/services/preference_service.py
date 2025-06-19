from typing import Dict, List
from app.models.preferences import (
    PhysicalConstraint,
    LanguagePreference,
    TripPurpose,
    Interest,
    Pace
)

class PreferenceService:
    def __init__(self):
        self.preference_details = {
            "physical_constraints": {
                PhysicalConstraint.NO_CONSTRAINTS: "No physical limitations",
                PhysicalConstraint.MOBILITY_ASSISTANCE: "Requires wheelchair accessibility and mobility assistance",
                PhysicalConstraint.VISUAL_IMPAIRMENT: "Visual impairment, needs audio descriptions and accessible formats",
                PhysicalConstraint.HEARING_IMPAIRMENT: "Hearing impairment, needs visual aids and written communication"
            },
            "language_preferences": {
                LanguagePreference.ENGLISH_PREFERRED: "English-speaking guides and services preferred",
                LanguagePreference.NATIVE_LANGUAGE_REQUIRED: "Local language immersion and native language speakers required",
                LanguagePreference.MULTILINGUAL_OK: "Multiple language options available, flexible with languages"
            },
            "trip_purposes": {
                TripPurpose.LEISURE: "Relaxation and enjoyment focused trip",
                TripPurpose.BUSINESS: "Business meetings, conferences, and work-related activities",
                TripPurpose.BLEISURE: "Mix of business and leisure activities",
                TripPurpose.RELOCATION: "Moving to a new location, exploring potential new home"
            },
            "interests": {
                Interest.SCUBA_DIVING: "Underwater exploration and diving experiences",
                Interest.MUSEUMS_ART: "Cultural experiences, art galleries, and museums",
                Interest.SHOPPING: "Shopping destinations, local markets, and retail experiences",
                Interest.NIGHTLIFE: "Nightlife, entertainment, bars, and evening activities",
                Interest.WILDLIFE_SAFARI: "Wildlife viewing, safari experiences, and nature conservation",
                Interest.SPORTS_ACTIVITIES: "Sports, outdoor activities, and adventure experiences",
                Interest.PHOTOGRAPHY: "Photography opportunities, scenic locations, and photo tours",
                Interest.FESTIVALS_EVENTS: "Local festivals, cultural events, and celebrations"
            },
            "pace": {
                Pace.RELAXED: "Leisurely pace with plenty of rest time and minimal rushing",
                Pace.BALANCED: "Balanced mix of activities and rest periods",
                Pace.PACKED: "Fast-paced itinerary with many activities and minimal downtime"
            }
        }

    def get_preference_details(self, category: str) -> Dict:
        """Get all details for a specific preference category."""
        return self.preference_details.get(category, {})

    def get_constraint_details(self, constraint: PhysicalConstraint) -> str:
        """Get details for a specific physical constraint."""
        return self.preference_details["physical_constraints"].get(constraint, "")

    def get_language_preference_details(self, preference: LanguagePreference) -> str:
        """Get details for a specific language preference."""
        return self.preference_details["language_preferences"].get(preference, "")

    def get_trip_purpose_details(self, purpose: TripPurpose) -> str:
        """Get details for a specific trip purpose."""
        return self.preference_details["trip_purposes"].get(purpose, "")

    def get_interest_details(self, interest: Interest) -> str:
        """Get details for a specific interest."""
        return self.preference_details["interests"].get(interest, "")

    def get_pace_details(self, pace: Pace) -> str:
        """Get details for a specific pace preference."""
        return self.preference_details["pace"].get(pace, "") 