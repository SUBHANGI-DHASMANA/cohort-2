import os
import re
import json
import uuid
import time
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import bigquery
import google.oauth2.credentials
import vertexai
from vertexai.generative_models import GenerativeModel
from analytics_pipeline import run_analytics_pipeline

app = FastAPI(title="FinPulse Retail Demand Intelligence API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ID = "cohort-2-500210"

def get_gcloud_credentials():
    try:
        token = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
        return google.oauth2.credentials.Credentials(token)
    except Exception:
        return None

# Initialize Vertex AI
credentials = get_gcloud_credentials()
vertexai.init(project=PROJECT_ID, location="us-central1", credentials=credentials)
chat_model = GenerativeModel("gemini-2.5-flash")

class PublishRequest(BaseModel):
    sku_id: int
    discount_rate: float
    promo_price: float
    risk_tier: str
    current_stock: int
    expected_lift: float
    recovered_margin: float

class ChatRequest(BaseModel):
    query: str

def extract_json(text):
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    
    # Try finding markdown code block
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
            
    match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
            
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
            
    return None

@app.get("/")
async def get_index():
    return FileResponse("dashboard.html")

@app.get("/dashboard.css")
async def get_css():
    return FileResponse("dashboard.css")

@app.get("/dashboard.js")
async def get_js():
    return FileResponse("dashboard.js")

@app.get("/markdown_recommendations.json")
async def get_recs_json():
    # If the file does not exist, trigger the pipeline to generate it
    if not os.path.exists("markdown_recommendations.json"):
        print("markdown_recommendations.json not found. Running analytics pipeline...")
        run_analytics_pipeline()
    return FileResponse("markdown_recommendations.json")

@app.get("/api/recommendations")
async def get_recommendations():
    if not os.path.exists("markdown_recommendations.json"):
        try:
            run_analytics_pipeline()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")
            
    try:
        with open("markdown_recommendations.json", "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read recommendations: {str(e)}")

@app.post("/api/publish")
async def publish_markdown(req: PublishRequest):
    try:
        creds = get_gcloud_credentials()
        if creds:
            client = bigquery.Client(project=PROJECT_ID, credentials=creds)
        else:
            client = bigquery.Client(project=PROJECT_ID)
            
        table_id = f"{PROJECT_ID}.retail_dataset.markdown_schedules"
        schedule_id = str(uuid.uuid4())
        
        rows_to_insert = [
            {
                "schedule_id": schedule_id,
                "sku_id": req.sku_id,
                "discount_rate": req.discount_rate,
                "promo_price": req.promo_price,
                "risk_tier": req.risk_tier,
                "current_stock": req.current_stock,
                "expected_lift": req.expected_lift,
                "recovered_margin": req.recovered_margin,
                "status": "ACTIVE"
            }
        ]
        
        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            raise HTTPException(status_code=500, detail=f"BigQuery Insert Errors: {errors}")
            
        return {"status": "success", "schedule_id": schedule_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inserting to BigQuery: {str(e)}")

@app.post("/api/chat")
async def chat_copilot(req: ChatRequest):
    try:
        first_prompt = f"""
You are the FinPulse Retail Copilot, an AI assistant integrated with BigQuery and NVIDIA RAPIDS.
You have access to a retail database in BigQuery under project `{PROJECT_ID}` and dataset `retail_dataset` containing:
1. `inventory`: Columns (sku_id, category, cost, price, current_stock, reorder_point, first_stock_date)
2. `stores`: Columns (store_id, city, region)
3. `transactions`: Columns (transaction_id, date, sku_id, store_id, quantity, price, discount)
4. `markdown_schedules`: Columns (schedule_id, sku_id, discount_rate, promo_price, risk_tier, current_stock, expected_lift, recovered_margin, published_at, status)

The user asks: "{req.query}"

Decide if answering this query requires writing and running a BigQuery SQL query on these tables.
If YES, respond ONLY with a JSON object of format:
{{"sql": "YOUR_SQL_QUERY"}}
Do not include any conversational text, explanation, or other markup except markdown code blocks. Ensure the SQL query is a valid standard SQL query on BigQuery. Target the correct tables using full format: `{PROJECT_ID}.retail_dataset.table_name`. 

If NO (e.g. greeting, general question not needing DB access), respond ONLY with a JSON object of format:
{{"text": "Your helpful response"}}
"""
        response = chat_model.generate_content(first_prompt)
        parsed = extract_json(response.text)
        
        if not parsed:
            # Fallback to direct conversational response
            return {"response": response.text.strip(), "sql": None, "gpu_simulated": False}
            
        if "sql" in parsed:
            sql_query = parsed["sql"]
            print(f"Executing Agent Generated SQL: {sql_query}")
            
            creds = get_gcloud_credentials()
            if creds:
                client = bigquery.Client(project=PROJECT_ID, credentials=creds)
            else:
                client = bigquery.Client(project=PROJECT_ID)
                
            # Execute SQL
            t0 = time.time()
            query_job = client.query(sql_query)
            results = query_job.result()
            
            # Format results
            rows = [dict(row) for row in results]
            execution_time = time.time() - t0
            
            # Use GPU simulation speeds: CPU time was ~20x of GPU time.
            gpu_time = execution_time * 0.05
            
            # Send results to Gemini for natural language generation
            second_prompt = f"""
You are the FinPulse Retail Copilot.
The user asked: "{req.query}"
The following data was retrieved from the database to answer their request:
{json.dumps(rows, default=str)}

Provide a concise, friendly, and professional response summarizing this data. Include formatted markdown tables if multiple products or numbers are returned. Point out key business insights like high-risk stock, margin recovery, or regional sales. Keep it clean.
"""
            final_response = chat_model.generate_content(second_prompt)
            
            return {
                "sql": sql_query,
                "gpu_simulated": True,
                "gpu_time": round(gpu_time, 3),
                "response": final_response.text.strip()
            }
        else:
            return {
                "sql": None,
                "gpu_simulated": False,
                "response": parsed.get("text", "I'm not sure how to answer that request.")
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
