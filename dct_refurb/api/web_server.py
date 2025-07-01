

import asyncio
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from services.worker_service import WorkerService

app = FastAPI()

# This is a client to the service mesh, running within the web server process.
service_client = WorkerService(name="WebServerClient")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/api/services")
async def get_services():
    """
    An API endpoint to get the list of active services from the mapper.
    """
    service_list = await asyncio.to_thread(service_client.list_peers)
    return service_list

@app.get("/hello")
async def hello():
    return {"message": "Hello, world!"}

@app.websocket("/ws/video")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WEB_SERVER: WebSocket client connected.")
    
    try:
        while True:
            # Use the service client to get a frame from a worker.
            image_data = await asyncio.to_thread(
                service_client.send_job_to_peer,
                "Worker-A",
                {"task": "request_image"},
                return_response=True # A new flag to indicate we want the response back
            )

            if image_data:
                # Encode the image data as base64 and send it over the WebSocket.
                b64_image = base64.b64encode(image_data).decode('utf-8')
                await websocket.send_text(f"data:image/jpeg;base64,{b64_image}")
            
            await asyncio.sleep(0.1) # Stream at ~10 FPS

    except WebSocketDisconnect:
        print("WEB_SERVER: WebSocket client disconnected.")
    except Exception as e:
        print(f"WEB_SERVER: Error in WebSocket: {e}")
    finally:
        if websocket.client_state.name != 'DISCONNECTED':
            await websocket.close()

if __name__ == "__main__":
    import uvicorn
    # This allows running the web server independently for testing.
    # The main.py will launch this as a separate process.
    uvicorn.run(app, host="0.0.0.0", port=8000)

