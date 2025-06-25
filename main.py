from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from openai import OpenAI
import os
import time

# ✅ Initialize OpenAI client properly
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

@app.post("/query-vector")
async def query_vector(request: Request):
    data = await request.json()
    query = data.get("query")
    
    try:
        # Create a thread
        thread = client.beta.threads.create()
        
        # Add the user's query as a message
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=query
        )
        
        # Use your existing assistant (no more creating new ones!)
        assistant_id = "asst_7ubnxrCiblgIUtQwFhKZb46g"
        
        # Run with your existing assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        
        # Wait for completion and get response
        while run.status == "in_progress" or run.status == "queued":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        
        # Get the assistant's response
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        response_content = messages.data[0].content[0].text.value
        
        return {"results": [response_content]}
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug-api")
async def debug_api():
    try:
        # Test if client can access your specific assistant
        assistant = client.beta.assistants.retrieve("asst_7ubnxrCiblgIUtQwFhKZb46g")
        return {
            "api_key_set": os.getenv("OPENAI_API_KEY") is not None,
            "api_key_preview": os.getenv("OPENAI_API_KEY")[:20] + "..." if os.getenv("OPENAI_API_KEY") else "None",
            "assistant_id": assistant.id,
            "assistant_name": assistant.name,
            "assistant_tools": [tool.type for tool in assistant.tools]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/.well-known/ai-plugin.json")
async def serve_manifest():
    return FileResponse("ai-plugin.json", media_type="application/json")

@app.get("/openapi.yaml")
async def serve_openapi():
    return FileResponse("openapi.yaml", media_type="text/yaml")
# Force assistant refresh Wed Jun 25 16:40:55 +04 2025
