import os
import shutil
from PIL import Image

def main():
    artifact_dir = r"C:\Users\akhiy\.gemini\antigravity-ide\brain\4977a1f1-cd77-4994-a9b2-52d8a09df80f"
    reports_plots_dir = "reports/plots"
    os.makedirs(reports_plots_dir, exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    # Locate screenshots in artifact folder, sorted alphabetically so the latest timestamp appears last
    files_in_artifact = sorted(os.listdir(artifact_dir))
    
    screenshot_map = {
        "industry_overview": None,
        "fund_performance": None,
        "investor_analytics": None,
        "sip_market_trends": None
    }
    
    for f in files_in_artifact:
        for k in screenshot_map.keys():
            if f.startswith(k) and f.endswith(".png"):
                screenshot_map[k] = os.path.join(artifact_dir, f)
                
    print("Found latest screenshots in artifacts:")
    for k, v in screenshot_map.items():
        print(f"  {k}: {v}")
        if not v:
            print(f"Error: Screenshot for {k} not found!")
            return
            
    # Target files in root and reports
    targets = {
        "industry_overview": {
            "root": "industry_overview.png",
            "report": os.path.join(reports_plots_dir, "industry_overview.png")
        },
        "fund_performance": {
            "root": "fund_performance.png",
            "report": os.path.join(reports_plots_dir, "fund_performance.png")
        },
        "investor_analytics": {
            "root": "investor_analytics.png",
            "report": os.path.join(reports_plots_dir, "investor_analytics.png")
        },
        "sip_market_trends": {
            "root": "sip_market_trends.png",
            "report": os.path.join(reports_plots_dir, "sip_market_trends.png")
        }
    }
    
    # Copy screenshots
    for key, paths in targets.items():
        src = screenshot_map[key]
        shutil.copy(src, paths["root"])
        shutil.copy(src, paths["report"])
        print(f"Copied latest {key} screenshot to workspace locations.")
        
    # Compile PNGs to PDF
    ordered_keys = ["industry_overview", "fund_performance", "investor_analytics", "sip_market_trends"]
    img_files = [targets[k]["root"] for k in ordered_keys]
    
    print("\nCompiling screenshots into Dashboard.pdf...")
    images = [Image.open(f).convert("RGB") for f in img_files]
    
    # Save as PDF in root
    images[0].save("Dashboard.pdf", save_all=True, append_images=images[1:])
    # Save as PDF in reports
    shutil.copy("Dashboard.pdf", "reports/Dashboard.pdf")
    
    print("[SUCCESS] Dashboard.pdf successfully re-compiled and saved in root and reports/ folders.")

if __name__ == "__main__":
    main()
