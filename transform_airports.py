import json
from collections import defaultdict

# Configuration
INPUT_FILE = './allAirports.json'
OUTPUT_FILE = './city_to_icao.json'

def sanitize_city_name(city: str) -> str:
    """Replace slashes and backslashes with underscores for Firestore document IDs"""
    return city.replace('/', '_').replace('\\', '_')

def transform_airports():
    try:
        print('📖 Reading airport data...')
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
        
        airports = data.get('airports', {})
        print(f'🔄 Processing {len(airports):,} airports...')
        
        # Group by city
        city_groups = defaultdict(list)
        processed = 0
        
        for code, airport in airports.items():
            city = airport.get('city', '').strip().lower()
            
            if not city:
                continue
            
            city_groups[city].append({
                'icao': airport.get('icao', code),
                'elevation': airport.get('elevation', 0),
                'country': airport.get('country'),
                'iata': airport.get('iata', '')
            })
            processed += 1
        
        # Pick best airport per city
        city_to_icao = {}
        duplicates = 0
        sanitized_conflicts = 0
        
        for city, airport_list in city_groups.items():
            if len(airport_list) > 1:
                duplicates += len(airport_list) - 1
                # Sort: prefer has IATA, then higher elevation
                airport_list.sort(key=lambda x: (bool(x['iata']), x['elevation']), reverse=True)
            
            # Sanitize city name for Firestore document ID
            sanitized_city = sanitize_city_name(city)
            
            # Check for conflicts after sanitization
            if sanitized_city in city_to_icao:
                sanitized_conflicts += 1
            
            city_to_icao[sanitized_city] = airport_list[0]['icao']
        
        print(f'✅ Processed {processed:,} airports')
        print(f'⚠️  Found {duplicates:,} duplicate cities (took primary airport)')
        if sanitized_conflicts > 0:
            print(f'⚠️  Found {sanitized_conflicts:,} conflicts after sanitization (last one wins)')
        print(f'📊 Created {len(city_to_icao):,} city->ICAO mappings')
        
        # Write output
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(city_to_icao, f, indent=2)
        print(f'💾 Saved to {OUTPUT_FILE}')
        
        # Show sample
        print('\n📋 Sample mappings:')
        for city, icao in list(city_to_icao.items())[:5]:
            print(f'  "{city}" -> {icao}')
        
    except FileNotFoundError:
        print(f'❌ Error: Could not find {INPUT_FILE}')
        exit(1)
    except json.JSONDecodeError:
        print(f'❌ Error: Invalid JSON in {INPUT_FILE}')
        exit(1)
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        exit(1)

if __name__ == '__main__':
    transform_airports()