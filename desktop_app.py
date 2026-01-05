import webview
import threading
import uvicorn
from backend.main import app
import sys
import os

def start_server():
    # Run the server on a specific port
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == '__main__':
    # Start the FastAPI server in a separate thread
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()

    # Create the native window
    webview.create_window(
        title="GST Reco AI",
        url="http://127.0.0.1:8000",
        width=1200,
        height=800,
        resizable=True
    )

    # Start the GUI loop
    webview.start()
