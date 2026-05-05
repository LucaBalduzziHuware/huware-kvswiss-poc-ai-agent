import os
import google.auth
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types
import asyncio

# Setup environment
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "sa-key.json"

async def test_identity():
    # We need to import app.agent after setting the env var to ensure credentials load correctly
    from app.agent import root_agent
    
    session_service = InMemorySessionService()
    user_id = "test-user-123"
    session = session_service.create_session_sync(user_id=user_id, app_name="test-identity")
    
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test-identity")
    
    # Prasing similar to what the user said
    queries = [
        "chi sono?",
        "Quali sono i miei dati tecnici di sistema?",
        "Qual è il mio ID utente nel sistema?",
        "Usa il tool get_system_user_info per dirmi chi sono",
        "Quali macchine sono monitorate?" # Test another tool to see if tool calling works at all
    ]
    
    for query in queries:
        print(f"\n--- TESTING QUERY: '{query}' ---")
        message = types.Content(
            role="user", parts=[types.Part.from_text(text=query)]
        )

        events = runner.run(
            new_message=message,
            user_id=user_id,
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.NONE), # None for easier debug
        )
        
        for event in events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"AGENT RESPONSE: {part.text}")
            
            # ADK Event structure check
            # print(f"DEBUG Event: {event}") # Uncomment to see full event structure
            
            # Check for function calls in the content parts (Gemini style)
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.function_call:
                        print(f"TOOL CALL DETECTED: {part.function_call.name}")

if __name__ == "__main__":
    asyncio.run(test_identity())
