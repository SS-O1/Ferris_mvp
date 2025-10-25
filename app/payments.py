# Payments stubbed for demo
def create_checkout_session(itinerary: dict, user_email: str) -> dict:
    """Simulated checkout for demo"""
    return {
        "checkout_url": "/success",
        "session_id": "demo_checkout_123"
    }
