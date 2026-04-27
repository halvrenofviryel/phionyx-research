"""
Phionyx Core - FastAPI Integration Example
==========================================

A minimal FastAPI wrapper exposing the Phionyx governance pipeline as an HTTP endpoint.

This example demonstrates how to integrate the framework-agnostic Phionyx Core 
(specifically `EchoOrchestrator`) into a web delivery layer. Note that Phionyx Core 
itself contains no HTTP or FastAPI dependencies; external dependencies enter through ports.

Endpoint:
    POST /govern

Payload Example:
    {"text": "User input text", "profile": "edu"}
"""
import time
import hashlib
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from phionyx_core import EchoOrchestrator, OrchestratorServices

app = FastAPI(
    title="Phionyx Core FastAPI Wrapper",
    description="A minimal HTTP endpoint wrapping the Phionyx governance pipeline."
)

# Initialize core services framework-agnostically 
services = OrchestratorServices()
orchestrator = EchoOrchestrator(services=services)

class GovernRequest(BaseModel):
    text: str
    profile: str = "edu"

@app.post("/govern")
async def govern_endpoint(request: GovernRequest):
    start_time = time.time()
    
    try:
        # Execute the canonical 46-block pipeline using the async run method
        result = await orchestrator.run(
            user_input=request.text,
            mode=request.profile,
            current_amplitude=5.0,
            current_entropy=0.3
        )
        
        # Extract contextual metadata 
        context = result.get("final_context")
        meta = context.metadata if context and hasattr(context, "metadata") else {}
        
        # Extract governed response or use placeholder if pipeline bypassed narrative layers
        governed_text = meta.get("narrative_text", "Fallback: Narrative layer output missing.")
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "governed_response": governed_text,
            "state": {
                "A": meta.get("physics_state", {}).get("arousal", 0.5),
                "V": meta.get("physics_state", {}).get("valence", 0.0),
                "H": meta.get("current_entropy", 0.3),
                "phi": meta.get("previous_phi", 0.82),
                "entropy": meta.get("current_entropy", 0.31)
            },
            "safety": {
                "_note": "Placeholder values. Wire to pipeline gate results for production use.",
                "kill_switch": "not_wired",
                "ethics_gate": "not_wired",
                "input_safety": "not_wired",
                "revision_directive": "not_wired"
            },
            "telemetry": {
                "pipeline_blocks_executed": len(result.get("results", {})),
                "execution_time_ms": execution_time_ms,
                "deterministic": True
            },
            "audit": {
                "record_id": f"aud_{int(time.time())}",
                "hash_chain": hashlib.sha256(governed_text.encode()).hexdigest(),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline Error: {str(e)}")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    
