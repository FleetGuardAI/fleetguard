import os
import urllib.request
from PIL import Image

IMAGE_DIR = os.path.join(os.getcwd(), "assets", "images")
os.makedirs(IMAGE_DIR, exist_ok=True)

# Curated list of high-quality logistics, trucking, maintenance, and telematics photos from Unsplash
PHOTO_TARGETS = {
    # Slide 1: Hero Truck on Highway
    "hero_truck_highway.jpg": "https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?auto=format&fit=crop&w=1600&q=85",
    # Slide 2: Fleet Depot / Yard
    "fleet_depot_yard.jpg": "https://images.unsplash.com/photo-1519003722824-194d4455a60c?auto=format&fit=crop&w=1200&q=85",
    # Slide 3: Three leakage thumbnails (Fuel, Detour, Downtime)
    "fuel_nozzle_dispense.jpg": "https://images.unsplash.com/photo-1545459720-aac8509eb02c?auto=format&fit=crop&w=800&q=85",
    "highway_route_corridor.jpg": "https://images.unsplash.com/photo-1506521781263-d8422e82f27a?auto=format&fit=crop&w=800&q=85",
    "workshop_truck_service.jpg": "https://images.unsplash.com/photo-1486006920555-c77dce18193b?auto=format&fit=crop&w=800&q=85",
    # Slide 4: Fuel Tank & Sensor Inspection
    "fuel_tank_inspection.jpg": "https://images.unsplash.com/photo-1527018607637-a23feff84888?auto=format&fit=crop&w=1200&q=85",
    # Slide 5: Route GPS & Highway Map
    "gps_navigation_highway.jpg": "https://images.unsplash.com/photo-1524661135-423995f22d0b?auto=format&fit=crop&w=1200&q=85",
    # Slide 6: Vehicle Breakdown & Workshop Mechanics
    "mechanic_engine_repair.jpg": "https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?auto=format&fit=crop&w=1200&q=85",
    # Slide 7: Driver Document & KYC Inspection
    "driver_document_kyc.jpg": "https://images.unsplash.com/photo-1450133064473-71024230f91b?auto=format&fit=crop&w=1200&q=85",
    # Slide 8: Hardware Telematics & GPS Tracker
    "telematics_gps_hardware.jpg": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=85",
    # Slide 9: Driver in Truck Cabin / Mobile App
    "driver_cabin_smartphone.jpg": "https://images.unsplash.com/photo-1508962914676-134849a727f0?auto=format&fit=crop&w=1200&q=85",
    # Slide 10: Logistics Warehouse Loading Dock
    "logistics_warehouse_dock.jpg": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=1200&q=85",
    # Slide 11: Tyres & Preventive Maintenance
    "truck_tyres_workshop.jpg": "https://images.unsplash.com/photo-1578844251758-2f71da64c96f?auto=format&fit=crop&w=1200&q=85",
    # Slide 12: Fleet Control Room / Operations Command
    "fleet_control_center.jpg": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1200&q=85",
    # Slide 14: Telematics Installation / Field Technician
    "technician_installation.jpg": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=1200&q=85",
    # Slide 17: Enterprise Cloud / Server Infrastructure
    "datacenter_security.jpg": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=1200&q=85",
    # Slide 18: Closing Inspiring Commercial Truck Highway
    "closing_commercial_truck.jpg": "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=1600&q=85"
}

def download_and_verify():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    success_count = 0
    
    for filename, url in PHOTO_TARGETS.items():
        file_path = os.path.join(IMAGE_DIR, filename)
        if os.path.exists(file_path) and os.path.getsize(file_path) > 10000:
            print(f"[EXISTS] {filename} ({os.path.getsize(file_path):,} bytes)")
            success_count += 1
            continue

        try:
            print(f"Downloading {filename}...")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response, open(file_path, 'wb') as out_file:
                out_file.write(response.read())
            
            # Verify with Pillow
            with Image.open(file_path) as img:
                w, h = img.size
                fmt = img.format
                print(f"  -> Verified: {w}x{h} {fmt} ({os.path.getsize(file_path):,} bytes)")
            success_count += 1
        except Exception as e:
            print(f"  -> FAILED to download {filename}: {e}")

    print(f"\nDownloaded and verified {success_count} / {len(PHOTO_TARGETS)} high-resolution photographs.")

if __name__ == "__main__":
    download_and_verify()
