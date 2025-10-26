from __future__ import annotations
from typing import Dict, Any, List
import re


class ConversationalAgent:
    """
    Smart conversational layer that handles open-ended questions
    and provides intelligent recommendations before slot-filling
    """
    
    def __init__(self):
        self.recommendation_db = {
            "ski": {
                "destinations": ["Lake Tahoe", "Mammoth", "Big Bear"],
                "pitch": "For skiing, I'd recommend Lake Tahoe (world-class slopes), Mammoth (epic powder), or Big Bear (closer drive from Bay Area)."
            },
            "beach": {
                "destinations": ["San Diego", "Santa Cruz", "Malibu", "Laguna Beach"],
                "pitch": "For beach vibes, you can't go wrong with San Diego (perfect weather), Santa Cruz (surf culture), Malibu (luxury coastal), or Laguna Beach (art + ocean)."
            },
            "wine": {
                "destinations": ["Napa", "Sonoma", "Paso Robles", "Healdsburg"],
                "pitch": "Wine country calls! Napa (premium tasting rooms), Sonoma (laid-back charm), Paso Robles (value + quality), or Healdsburg (boutique wineries)."
            },
            "hiking": {
                "destinations": ["Big Sur", "Yosemite", "Joshua Tree", "Sequoia"],
                "pitch": "Trail time! Big Sur (coastal hikes), Yosemite (iconic views), Joshua Tree (desert landscapes), or Sequoia (giant trees)."
            },
            "city": {
                "destinations": ["San Francisco", "Los Angeles", "San Diego", "Oakland"],
                "pitch": "City escape? San Francisco (culture + food), Los Angeles (entertainment), San Diego (laid-back urban), or Oakland (arts + nightlife)."
            },
            "relaxing": {
                "destinations": ["Carmel", "Ojai", "Mendocino", "Half Moon Bay"],
                "pitch": "Need to unwind? Carmel (coastal zen), Ojai (spa town), Mendocino (clifftop serenity), or Half Moon Bay (quiet beach town)."
            }
        }
    
    def detect_request_for_recommendation(self, message: str) -> bool:
        """Detect if user is asking for recommendations"""
        msg = message.lower()
        
        asking_patterns = [
            "where should",
            "where would you",
            "recommend",
            "suggest",
            "what do you think",
            "where do i",
            "where can i",
            "best place",
            "good place",
            "where to go"
        ]
        
        return any(pattern in msg for pattern in asking_patterns)
    
    def detect_activity_request(self, message: str) -> str:
        """Detect what activity user is asking about"""
        msg = message.lower()
        
        if any(word in msg for word in ["ski", "skiing", "snow", "snowboard"]):
            return "ski"
        elif any(word in msg for word in ["beach", "ocean", "surf", "sand", "coast"]):
            return "beach"
        elif any(word in msg for word in ["wine", "vineyard", "tasting", "winery"]):
            return "wine"
        elif any(word in msg for word in ["hike", "hiking", "trail", "mountain"]):
            return "hiking"
        elif any(word in msg for word in ["city", "urban", "downtown", "museum"]):
            return "city"
        elif any(word in msg for word in ["relax", "peaceful", "quiet", "spa", "chill"]):
            return "relaxing"
        
        return None
    
    def generate_recommendation_response(self, message: str, context: Any) -> Dict[str, Any]:
        """Generate smart recommendation response"""
        
        # Detect activity
        activity = self.detect_activity_request(message)
        
        if activity and activity in self.recommendation_db:
            rec = self.recommendation_db[activity]
            
            response_text = (
                f"{rec['pitch']}\n\n"
                f"Which one sounds good to you?"
            )
            
            return {
                "text": response_text,
                "itinerary": None,
                "state": "AWAITING_DESTINATION_CHOICE",
                "needed": ["destination"],
                "quick_replies": rec["destinations"] + ["Show me more options"]
            }
        
        # Generic recommendation if no specific activity detected
        return self.generate_generic_recommendation(message, context)
    
    def generate_generic_recommendation(self, message: str, context: Any) -> Dict[str, Any]:
        """Handle generic 'where should I go' questions"""
        
        response_text = (
            "Great question! What vibe are you going for?\n\n"
            "🎿 Skiing & Snow\n"
            "🏖️ Beach & Ocean\n"
            "🍷 Wine Country\n"
            "🥾 Hiking & Nature\n"
            "🏙️ City Escape\n"
            "😌 Relaxing Retreat"
        )
        
        return {
            "text": response_text,
            "itinerary": None,
            "state": "AWAITING_ACTIVITY_CHOICE",
            "needed": ["activity"],
            "quick_replies": ["Skiing", "Beach", "Wine", "Hiking", "City", "Relaxing"]
        }
    
    def handle_follow_up_question(self, message: str, context: Any) -> Dict[str, Any]:
        """Handle conversational follow-ups"""
        msg = message.lower()
        
        # "Tell me more about X"
        if "more about" in msg or "tell me" in msg:
            return self.provide_destination_details(message, context)
        
        # "What else" / "Other options"
        if any(phrase in msg for phrase in ["what else", "other option", "more option", "something else"]):
            return self.provide_alternative_recommendations(context)
        
        # "Why" questions
        if msg.startswith("why"):
            return self.explain_recommendation(context)
        
        return None
    
    def provide_destination_details(self, message: str, context: Any) -> Dict[str, Any]:
        """Provide details about a specific destination"""
        
        destination_info = {
            "lake tahoe": "Lake Tahoe is perfect for skiing - world-class resorts like Palisades and Heavenly, stunning lake views, and great après-ski. Best for: winter sports enthusiasts.",
            "mammoth": "Mammoth Mountain offers epic powder, long season (Nov-June), and authentic mountain town vibes. Best for: serious skiers who want the real deal.",
            "big bear": "Big Bear is your closest ski option from the Bay Area - family-friendly, affordable, and great for weekend trips. Best for: quick getaways.",
            "san diego": "San Diego = perfect weather year-round, amazing beaches, incredible tacos, and laid-back vibes. Best for: beach lovers who want sun guaranteed.",
            "napa": "Napa Valley is premium wine country - world-renowned wineries, Michelin-star restaurants, and luxury accommodations. Best for: special occasions."
        }
        
        for dest, info in destination_info.items():
            if dest in message.lower():
                return {
                    "text": f"{info}\n\nWant to book a place there?",
                    "itinerary": None,
                    "state": "AWAITING_CONFIRMATION",
                    "quick_replies": [f"Yes, book {dest.title()}", "Tell me about another place"]
                }
        
        return None
    
    def provide_alternative_recommendations(self, context: Any) -> Dict[str, Any]:
        """Show more destination options"""
        
        all_destinations = [
            "Santa Barbara", "Palm Springs", "Santa Monica", 
            "Monterey", "Carmel", "Santa Cruz", "Ojai"
        ]
        
        return {
            "text": "Here are some other great options:\n\n🌴 Santa Barbara - Coastal charm\n🏜️ Palm Springs - Desert oasis\n🎨 Santa Monica - Beach + city\n🐋 Monterey - Aquarium + coast\n\nWhich sounds interesting?",
            "itinerary": None,
            "state": "AWAITING_DESTINATION_CHOICE",
            "quick_replies": all_destinations[:4]
        }
    
    def explain_recommendation(self, context: Any) -> Dict[str, Any]:
        """Explain why we recommended something"""
        
        return {
            "text": "Great question! I base recommendations on:\n\n✨ Your trip style (skiing = Tahoe)\n💰 Typical budgets ($800-1000)\n⭐ Highest-rated properties\n📍 Accessibility from Bay Area\n\nWhat matters most to you?",
            "itinerary": None,
            "state": "COLLECTING_PREFERENCES",
            "quick_replies": ["Best value", "Highest rated", "Closest drive", "Most unique"]
        }
