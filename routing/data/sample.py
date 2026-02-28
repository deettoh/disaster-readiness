"""Generates structured JSON sample test cases representing realistic disaster evacuation scenarios across Petaling Jaya."""

import json


def generate_pj_test_cases():
    """Generates realistic disaster-evacuation scenarios for Petaling Jaya and saves to 'test_scenarios.json' for use in routing tests."""
    # Coordinates for Petaling Jaya Hotspots (Starts) and Shelters (Ends)
    scenarios = [
        {
            "id": "scenario_01",
            "name": "Sungai Way Flash Flood",
            "start_point": {"name": "Kg Baru Sg Way Residential", "lon": 101.6185, "lat": 3.0890},
            "end_point": {"name": "Dewan Serbaguna Sungai Way", "lon": 101.6208, "lat": 3.0867},
            "description": "High-density residential evacuation to the nearest community hall."
        },
        {
            "id": "scenario_02",
            "name": "Damansara Jaya Urban Evac",
            "start_point": {"name": "SS22 Housing Area", "lon": 101.6130, "lat": 3.1295},
            "end_point": {"name": "Dewan Atria Damansara Jaya", "lon": 101.6170, "lat": 3.1270},
            "description": "Navigating through commercial/urban grid during heavy rain."
        },
        {
            "id": "scenario_03",
            "name": "PJS 6 Emergency Move",
            "start_point": {"name": "Mentari Court Area", "lon": 101.6110, "lat": 3.0765},
            "end_point": {"name": "Dewan Komuniti PJS 6", "lon": 101.6153, "lat": 3.0808},
            "description": "Low-lying area near Federal Highway moving to higher ground."
        },
        {
            "id": "scenario_04",
            "name": "Section 14 Hospital Route",
            "start_point": {"name": "Jalan Semangat Junction", "lon": 101.6350, "lat": 3.1110},
            "end_point": {"name": "Dewan Komuniti Section 19", "lon": 101.6321, "lat": 3.1190},
            "description": "Testing routing connectivity near major healthcare hubs."
        },
        {
            "id": "scenario_05",
            "name": "Southern PJ Safety Run",
            "start_point": {"name": "PJS 2 Taman Maju Jaya", "lon": 101.6390, "lat": 3.0810},
            "end_point": {"name": "D'Buana Hall", "lon": 101.6371, "lat": 3.0787},
            "description": "Testing short-path 'Snapping' logic in the southern boundary."
        }
    ]

    output_file = "pj_test_scenarios.json"

    try:
        with open(output_file, 'w') as f:
            json.dump(scenarios, f, indent=4)

        print(f"Successfully generated {len(scenarios)} scenarios in '{output_file}'")
        print("\n--- Summary of Test Pairs ---")
        for s in scenarios:
            print(f"[{s['name']}]")
            print(f"   Start: {s['start_point']['lon']}, {s['start_point']['lat']}")
            print(f"   End:   {s['end_point']['lon']}, {s['end_point']['lat']}")
            print(f"   Goal:  {s['description']}\n")

    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    generate_pj_test_cases()
