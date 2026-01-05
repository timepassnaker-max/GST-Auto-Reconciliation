from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import io
import os
from backend.reconcile import process_reconciliation
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount static directory
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

import shutil
import uuid

# Create temp directory if it doesn't exist
os.makedirs("backend/temp", exist_ok=True)

# Mount temp static for downloads
app.mount("/download", StaticFiles(directory="backend/temp"), name="download")

@app.get("/")
def read_root():
    return FileResponse('backend/static/index.html')

from fastapi.concurrency import run_in_threadpool

@app.post("/reconcile")
@app.post("/api/reconcile")
async def reconcile_files(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel file.")
    
    try:
        print(f"Received file: {file.filename}") # Debug log
        contents = await file.read()
        print(f"File read complete. Size: {len(contents)} bytes. Starting processing...")
        
        # Run CPU-intensive task in a separate thread to avoid blocking the server
        output_stream, stats = await run_in_threadpool(process_reconciliation, contents)
        print("Processing complete.")
        
        # Save to temp file
        filename = f"GST_Reco_{uuid.uuid4().hex[:8]}.xlsx"
        filepath = os.path.join("backend/temp", filename)
        
        with open(filepath, "wb") as f:
            f.write(output_stream.getvalue())
            
        return {
            "status": "success",
            "stats": stats,
            "download_url": f"/download/{filename}",
            "filename": filename
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        # Return a structured error that the frontend can parse
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

@app.get("/api/template")
async def get_template():
    # Create a blank Excel file in memory
    output = io.BytesIO()
    columns = ['GSTIN', 'Name', 'Invoice number', 'Invoice Date', 'Taxable Value', 'IGST', 'CGST', 'SGST', 'Remarks']
    
    # Create empty DataFrame
    df = pd.DataFrame(columns=columns)
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Portal data', index=False)
        df.to_excel(writer, sheet_name='Books data', index=False)
        
        # Optional: Adjust column widths to make it look nice
        for sheet in ['Portal data', 'Books data']:
            worksheet = writer.sheets[sheet]
            worksheet.set_column('A:I', 15)

    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=GST_Reco_Template.xlsx"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
