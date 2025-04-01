import requests
import json
from pathlib import Path

SERVICE_ENDPOINTS = {
    "text2speech": "http://127.0.0.1:5001/process",  
    "conversion": "http://127.0.0.1:5002/process",
    "profanity": "http://127.0.0.1:5003/process",
    "censor": "http://127.0.0.1:5004/process",
    "compression": "http://127.0.0.1:5005/process"
}


def run_workflow(message):
    try:
        # 1. Text-to-Speech
        print("Starting Text-to-Speech...")
        tts_resp = requests.post(SERVICE_ENDPOINTS["text2speech"], 
                               json={"message": message}, timeout=30)
        tts_resp.raise_for_status()
        
        # 2. Conversion
        print("Converting audio...")
        conv_resp = requests.post(SERVICE_ENDPOINTS["conversion"],
                                data=tts_resp.content, timeout=30)
        conv_resp.raise_for_status()
        
        # 3. Profanity Detection
        print("Detecting profanity...")
        prof_resp = requests.post(SERVICE_ENDPOINTS["profanity"],
                                json={"message": message}, timeout=30)
        prof_resp.raise_for_status()
        indexes = prof_resp.json()["indexes"]
        
        # 4. Censor
        print("Censoring audio...")
        censor_resp = requests.post(SERVICE_ENDPOINTS["censor"],
                                  files={
                                      "to_censor": ("audio.wav", conv_resp.content),
                                      "indexes": ("indexes.json", json.dumps(indexes))
                                  }, timeout=30)
        censor_resp.raise_for_status()
        
        # 5. Compression
        print("Compressing audio...")
        comp_resp = requests.post(SERVICE_ENDPOINTS["compression"],
                                files={"to_compress": ("censored.wav", censor_resp.content)},
                                timeout=30)
        comp_resp.raise_for_status()
        
        # Save output
        Path("final_output.wav").write_bytes(comp_resp.content)
        print("✅ Pipeline completed successfully!")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {str(e)}")
        # Debugging help:
        print("\nDebug Info:")
        print(f"Text-to-Speech status: {tts_resp.status_code if 'tts_resp' in locals() else 'N/A'}")
        print(f"Conversion status: {conv_resp.status_code if 'conv_resp' in locals() else 'N/A'}")
        print(f"Profanity Detection status: {prof_resp.status_code if 'prof_resp' in locals() else 'N/A'}")
        print(f"Censor status: {censor_resp.status_code if 'censor_resp' in locals() else 'N/A'}")
        

if __name__ == "__main__":
    # run_workflow("This is a damn mess. I can't believe this stupid fucking system keeps screwing up—it's absolute bullshit! Every fucking time I try to get something done, some idiot comes along and fucks everything up. What the hell is wrong with this piece-of-shit setup? It's like no one gives a damn about making things work properly. Shit, I'm so sick of dealing with this crap!")
    run_workflow("This is a damn mess. I can't believe this stupid fucking system keeps screwing up—it's ")
    # run_workflow("absolute bullshit! Every fucking time I try to get something done, ")
    # run_workflow("some idiot comes along and fucks everything up. What the hell is wrong with this piece-of-shit setup? ")
    # run_workflow("It's like no one gives a damn about making things work properly. ")
    # run_workflow("Shit, I'm so sick of dealing with this crap!")