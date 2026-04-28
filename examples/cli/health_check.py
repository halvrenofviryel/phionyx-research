"""
Phionyx Core - CLI Health Check
===============================
A standalone diagnostic script to verify the installation, 
pipeline block integrity, and orchestrator execution.
"""
import sys
import time
import asyncio
import logging

#Suppress internal library logging so only health check output is printed
logging.disable(logging.CRITICAL)

try:
    import phionyx_core
    from phionyx_core import EchoOrchestrator, OrchestratorServices
    from phionyx_core.orchestrator.block_factory import create_all_blocks
    from phionyx_core.contracts.telemetry import get_canonical_blocks, get_contract_version
    from phionyx_core.profiles.profile_manager import ProfileManager
except ImportError as e:
    print(f"Error importing phionyx_core: {e}")
    print("Make sure it is installed via 'pip install -e .'")
    sys.exit(1)

async def run_smoke_test():
    """Runs a minimal pipeline execution to verify orchestrator health."""
    # Initialize framework-agnostic core services
    services = OrchestratorServices()
    orchestrator = EchoOrchestrator(services=services)
    
    # Wire up all pipeline blocks via the block factory
    blocks = create_all_blocks(services=services)
    for block in blocks.values():
        orchestrator.register_block(block)
    
    start_time = time.time()
    
    # Execute the pipeline with a dummy input
    result = await orchestrator.run(
        user_input="health check test",
        mode="edu"
    )
    
    execution_time_ms = int((time.time() - start_time) * 1000)
    return execution_time_ms, result

async def main():
    print("Phionyx Core Health Check")
    print("========================")
    
    # Version
    version = getattr(phionyx_core, "__version__", "unknown")
    print(f"Version:          {version}")
    
    # Pipeline blocks
    blocks = get_canonical_blocks()
    contract_version = get_contract_version()
    print(f"Pipeline blocks:  {len(blocks)} (contract v{contract_version})")
    
    # Profiles loaded
    try:
        expected_profiles = ["edu", "game", "clinical"]
        loaded = []
        
        for p in expected_profiles:
            try:
                ProfileManager.create_profile(p)
                loaded.append(p)
            except Exception:
                continue
                
        if len(loaded) == 0:
            print("Profiles loaded:  FAIL (Could not load any core profiles)")
            sys.exit(1)
            
        print(f"Profiles loaded:  {len(loaded)} ({', '.join(loaded)})")
        
    except Exception as e:
        print(f"Profiles loaded:  FAIL (Manager Error: {str(e)})")
        sys.exit(1)


    # Smoke test
    try:
        elapsed_ms, result = await run_smoke_test()
        
        # Verify the pipeline returned a valid structure and actually executed blocks
        if result and "final_context" in result:
            all_results = result.get("results", {})
            skipped = result.get("skipped_blocks", [])
            executed_count = len(all_results) - sum(
                1 for br in all_results.values()
                if getattr(br, "status", None) in ("skipped", "error")
            )
            if executed_count <= 0 or len(skipped) == len(blocks):
                print("Smoke test:       FAIL (Pipeline returned but no blocks executed)")
                sys.exit(1)
            print(f"Smoke test:       PASS (pipeline executed in {elapsed_ms}ms)")
            sys.exit(0)
        else:
            print("Smoke test:       FAIL (Pipeline executed but returned invalid structure)")
            sys.exit(1)
            
    except Exception as e:
        print(f"Smoke test:       FAIL (Exception: {str(e)})")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
    