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
        
        # Create an assistant with your vector store
        assistant = client.beta.assistants.create(
            name="Vector Store Assistant",
            instructions="You help answer questions using the vector store.",
            model="gpt-4o-mini",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": ["vs_68551a089ac481918cb74bad43bad40a"]}}
        )
        
        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
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
        # Test if client can list vector stores
        vector_stores = client.beta.vector_stores.list()
        return {
            "api_key_set": os.getenv("OPENAI_API_KEY") is not None,
            "api_key_preview": os.getenv("OPENAI_API_KEY")[:20] + "..." if os.getenv("OPENAI_API_KEY") else "None",
            "vector_stores_found": len(vector_stores.data),
            "vector_store_ids": [vs.id for vs in vector_stores.data]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/.well-known/ai-plugin.json")
async def serve_manifest():
    return FileResponse("ai-plugin.json", media_type="application/json")

@app.get("/openapi.yaml")
async def serve_openapi():
    return FileResponse("openapi.yaml", media_type="text/yaml")
