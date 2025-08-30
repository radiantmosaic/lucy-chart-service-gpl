#!/usr/bin/env python3
"""
Kerykeion Chart Generator for GPL Chart Service
Copyright (C) 2024 Lucy Bot Chart Service

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Features:
- Generates wheel-only SVG charts using Kerykeion library.
- Fixes the "all black SVG" issue by inlining CSS variables.
- Suppresses Kerykeion's stdout/stderr so only SVG is printed.
- On errors, prints a fallback error SVG to stdout and logs full traceback to stderr (flushed).
- Disables Chiron and Lilith in chart generation.
- Supports synastry charts when synastry_data is provided.
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from typing import Dict, Any


def map_country_to_code(country: str) -> str:
    """Map country names to ISO country codes for Kerykeion."""
    if not country or len(country) <= 2:
        return country or 'US'
    
    country_mapping = {
        'United States': 'US', 'USA': 'US',
        'United Kingdom': 'GB', 'UK': 'GB',
        'Canada': 'CA', 'Australia': 'AU',
        'Germany': 'DE', 'France': 'FR', 'Italy': 'IT',
        'Spain': 'ES', 'Netherlands': 'NL', 'Belgium': 'BE',
        'Switzerland': 'CH', 'Austria': 'AT', 'Japan': 'JP',
        'China': 'CN', 'India': 'IN', 'Brazil': 'BR', 'Mexico': 'MX',
        'Argentina': 'AR', 'Russia': 'RU', 'Norway': 'NO',
        'Sweden': 'SE', 'Denmark': 'DK', 'Finland': 'FI',
        'Poland': 'PL', 'Czech Republic': 'CZ', 'Hungary': 'HU',
        'Ireland': 'IE', 'Portugal': 'PT', 'Greece': 'GR',
        'Turkey': 'TR', 'Israel': 'IL', 'Egypt': 'EG',
        'South Africa': 'ZA', 'New Zealand': 'NZ',
        'South Korea': 'KR', 'Thailand': 'TH', 'Singapore': 'SG',
        'Philippines': 'PH', 'Malaysia': 'MY', 'Indonesia': 'ID',
        'Vietnam': 'VN', 'Chile': 'CL', 'Colombia': 'CO',
        'Peru': 'PE', 'Venezuela': 'VE', 'Ukraine': 'UA',
        'Romania': 'RO', 'Bulgaria': 'BG', 'Croatia': 'HR',
        'Serbia': 'RS', 'Slovenia': 'SI', 'Slovakia': 'SK',
        'Lithuania': 'LT', 'Latvia': 'LV', 'Estonia': 'EE',
        'Iceland': 'IS', 'Luxembourg': 'LU', 'Malta': 'MT',
        'Cyprus': 'CY'
    }
    return country_mapping.get(country, 'US')


def parse_birth_data(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse birth data into Kerykeion format."""
    birth_date_str = chart_data.get('birth_date')
    if isinstance(birth_date_str, str):
        if 'T' in birth_date_str:
            birth_datetime = datetime.fromisoformat(birth_date_str.replace('Z', '+00:00'))
        else:
            birth_datetime = datetime.strptime(birth_date_str, '%Y-%m-%d')
    else:
        raise ValueError(f"Invalid birth_date format: {birth_date_str}")
    
    birth_time_str = chart_data.get('birth_time', '12:00:00')
    if isinstance(birth_time_str, str):
        if len(birth_time_str) == 5:  # HH:MM
            hour, minute = map(int, birth_time_str.split(':'))
        elif len(birth_time_str) == 8:  # HH:MM:SS
            hour, minute = map(int, birth_time_str.split(':')[:2])
        else:
            hour, minute = 12, 0
    else:
        hour, minute = 12, 0

    city = chart_data.get('birth_city') or 'London'
    country = chart_data.get('birth_country') or 'GB'
    country_code = map_country_to_code(country)

    return {
        'name': chart_data.get('name', 'Chart'),
        'year': birth_datetime.year,
        'month': birth_datetime.month,
        'day': birth_datetime.day,
        'hour': hour,
        'minute': minute,
        'city': city,
        'nation': country_code
    }


def map_house_system(house_system: str) -> str:
    """Map house system names to Kerykeion codes."""
    return {
        'placidus': 'P',
        'whole-sign': 'W',
        'campanus': 'C'
    }.get(house_system, 'P')


def get_active_points(rulership: str, is_transit: bool = False) -> list:
    """Get active points based on rulership system."""
    if rulership == 'traditional':
        # Traditional 7 planets (no outer planets, no nodes)
        planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
    else:  # modern (default)
        # Modern planets including outer planets and nodes
        planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
                  "Uranus", "Neptune", "Pluto", "Mean_Node"]
    
    # For pure transit charts, exclude ALL house cusps and angles
    if is_transit:
        # Only return planets - no house cusps, no angles, no asc/mc
        return planets
    else:
        # Include angles for natal/synastry charts
        angles = ["Ascendant", "Medium_Coeli"]
        return planets + angles


def generate_chart(input_data: Dict[str, Any]) -> str:
    """Generate wheel-only SVG chart using Kerykeion with Chiron and Lilith disabled."""
    from kerykeion import AstrologicalSubject, KerykeionChartSVG, KrInstance
    
    # Check if this is a transit/date-only chart
    is_transit = input_data.get('is_transit', False)
    original_methods = {}
    
    # If it's a transit chart, monkeypatch KerykeionChartSVG to disable house drawing
    if is_transit:
        # Save and replace ALL methods that might draw houses
        for method_name in dir(KerykeionChartSVG):
            if any(word in method_name.lower() for word in ['house', 'cusp', 'division']):
                if hasattr(KerykeionChartSVG, method_name) and callable(getattr(KerykeionChartSVG, method_name)):
                    original_methods[method_name] = getattr(KerykeionChartSVG, method_name)
                    setattr(KerykeionChartSVG, method_name, lambda self, *a, **k: None)
        
        import logging
        logging.warning(f"TRANSIT DEBUG: Monkeypatched {len(original_methods)} methods: {list(original_methods.keys())}")
        print(f"TRANSIT DEBUG: About to monkeypatch for transit chart")  # Try stdout too
    
    # Create a custom AstrologicalSubject that doesn't calculate houses for transits
    class TransitSubject(AstrologicalSubject):
        """Custom AstrologicalSubject that skips house calculations for transit charts."""
        
        def __init__(self, *args, **kwargs):
            self._is_transit = kwargs.pop('_is_transit', False)
            super().__init__(*args, **kwargs)
            
        def houses(self):
            """Override houses method to return empty dict for transit charts."""
            if self._is_transit:
                return {}
            else:
                return super().houses()
        
        def _calculate_houses(self):
            """Override house calculation for transit charts."""
            if self._is_transit:
                # Skip house calculations entirely - just return empty dict
                self.houses_list = []
                return {}
            else:
                return super()._calculate_houses()
    
    # Create a custom KerykeionChartSVG that doesn't draw houses for transit charts
    class NoHousesChartSVG(KerykeionChartSVG):
        """Custom chart SVG that completely skips house drawing for transit/date-only charts."""
        
        def __init__(self, *args, **kwargs):
            self._skip_houses = kwargs.pop('_skip_houses', False)
            super().__init__(*args, **kwargs)
            
            # If skipping houses, override ALL possible drawing methods dynamically
            if self._skip_houses:
                # Get all methods that might draw houses
                for method_name in dir(self):
                    if any(word in method_name.lower() for word in ['house', 'cusp', 'division']) and callable(getattr(self, method_name)):
                        # Create a no-op function for this method
                        setattr(self, method_name, lambda *a, **k: None)
        
        def makeWheelOnlySVG(self, *args, **kwargs):
            """Override the main method to prevent any house drawing."""
            if self._skip_houses:
                # Clear houses from all subjects before generating
                for attr in ['first_subject', 'subject', 'user']:
                    if hasattr(self, attr):
                        subj = getattr(self, attr)
                        if subj:
                            subj.houses_list = []
                            subj.houses_dict = {}
                            if hasattr(subj, 'cusps'):
                                subj.cusps = []
            
            # Call parent method
            return super().makeWheelOnlySVG(*args, **kwargs)

    chart_data = input_data.get('chart_data', {})
    if not chart_data:
        raise ValueError("No chart_data provided")
    
    user_preferences = input_data.get('user_preferences', {})
    synastry_data = input_data.get('synastry_data')
    is_transit = input_data.get('is_transit', False)
    
    # Debug output
    print(f"DEBUG: Chart generation starting - is_transit={is_transit}, name={chart_data.get('name', 'Unknown')}", file=sys.stderr)
    
    # DEBUG: Inspect KerykeionChartSVG methods when transit is requested
    if is_transit:
        house_methods = [m for m in dir(KerykeionChartSVG) if 'house' in m.lower()]
        print(f"DEBUG: Methods with 'house': {house_methods}", file=sys.stderr)
        
        draw_methods = [m for m in dir(KerykeionChartSVG) if 'draw' in m.lower()]
        print(f"DEBUG: Methods with 'draw': {draw_methods}", file=sys.stderr)
        
        # Look for the makeWheelOnlySVG method and try to see what it does
        print(f"DEBUG: makeWheelOnlySVG exists: {hasattr(KerykeionChartSVG, 'makeWheelOnlySVG')}", file=sys.stderr)
    
    sys.stderr.flush()
    birth_info = parse_birth_data(chart_data)

    latitude = chart_data.get('birth_latitude')
    longitude = chart_data.get('birth_longitude')
    timezone = chart_data.get('birth_timezone')

    house_system = user_preferences.get('houseSystem', 'placidus')
    zodiac = user_preferences.get('zodiac', 'tropical')
    rulership = user_preferences.get('rulership', 'modern')
    kerykeion_house_system = map_house_system(house_system)

    zodiac_type, sidereal_mode = "Tropic", None
    if zodiac == 'lahiri-vedic':
        zodiac_type, sidereal_mode = "Sidereal", "LAHIRI"

    common_params = {
        'name': birth_info['name'],
        'year': birth_info['year'],
        'month': birth_info['month'],
        'day': birth_info['day'],
        'hour': birth_info['hour'],
        'minute': birth_info['minute'],
        'houses_system_identifier': kerykeion_house_system,
        'zodiac_type': zodiac_type,
        'disable_chiron': True  # Disable Chiron calculations
    }
    if sidereal_mode:
        common_params['sidereal_mode'] = sidereal_mode

    if latitude and longitude and latitude != 0 and longitude != 0:
        if is_transit:
            first_subject = TransitSubject(
                lng=float(longitude), lat=float(latitude),
                tz_str=timezone if timezone else "UTC",
                city=birth_info['city'], _is_transit=True, **common_params
            )
        else:
            first_subject = AstrologicalSubject(
                lng=float(longitude), lat=float(latitude),
                tz_str=timezone if timezone else "UTC",
                city=birth_info['city'], **common_params
            )
    else:
        if is_transit:
            first_subject = TransitSubject(
                city=birth_info['city'], nation=birth_info['nation'], _is_transit=True, **common_params
            )
        else:
            first_subject = AstrologicalSubject(
                city=birth_info['city'], nation=birth_info['nation'], **common_params
            )

    # Get active points based on rulership system
    active_points = get_active_points(rulership, is_transit)
    
    # Wipe house data for transit/date-only charts so chart drawer has nothing to render  
    if is_transit:
        # Comprehensive house data wiping - this prevents houses from being drawn at all
        first_subject.houses_list = []
        first_subject.houses_dict = {}
        
        # Clear cusps which are used for house divisions
        if hasattr(first_subject, "cusps"):
            first_subject.cusps = []
        if hasattr(first_subject, "house_cusps"):
            first_subject.house_cusps = []
        if hasattr(first_subject, "house_cusps_list"):
            first_subject.house_cusps_list = []
            
        # Clear any other house-related attributes
        if hasattr(first_subject, 'houses'):
            first_subject.houses = {}
        if hasattr(first_subject, '_houses'):
            first_subject._houses = {}
        if hasattr(first_subject, '_house_cusps'):
            first_subject._house_cusps = []
        if hasattr(first_subject, '_cusps'):
            first_subject._cusps = []
        if hasattr(first_subject, 'house_positions'):
            first_subject.house_positions = []
            
        print(f"DEBUG: Wiped all house data for transit chart: {first_subject.name}", file=sys.stderr)
        sys.stderr.flush()

    with tempfile.TemporaryDirectory() as temp_dir:
        if synastry_data:
            # Check if this is a transit chart (synastry data with transit in name)
            is_transit_chart = (synastry_data.get('name', '').startswith('Transit ') or 
                               synastry_data.get('name', '').startswith('Transits '))
            
            # Parse synastry/transit data
            synastry_info = parse_birth_data(synastry_data)
            synastry_latitude = synastry_data.get('birth_latitude')
            synastry_longitude = synastry_data.get('birth_longitude')
            synastry_timezone = synastry_data.get('birth_timezone')
            
            if is_transit_chart:
                print(f"DEBUG: Creating transit chart - natal vs transits", file=sys.stderr)

            synastry_params = {
                'name': synastry_info['name'],
                'year': synastry_info['year'],
                'month': synastry_info['month'],
                'day': synastry_info['day'],
                'hour': synastry_info['hour'],
                'minute': synastry_info['minute'],
                'houses_system_identifier': kerykeion_house_system,
                'zodiac_type': zodiac_type,
                'disable_chiron': True
            }
            if sidereal_mode:
                synastry_params['sidereal_mode'] = sidereal_mode

            if synastry_latitude and synastry_longitude and synastry_latitude != 0 and synastry_longitude != 0:
                second_subject = AstrologicalSubject(
                    lng=float(synastry_longitude), lat=float(synastry_latitude),
                    tz_str=synastry_timezone if synastry_timezone else "UTC",
                    city=synastry_info['city'], **synastry_params
                )
            else:
                second_subject = AstrologicalSubject(
                    city=synastry_info['city'], nation=synastry_info['nation'], **synastry_params
                )

            # Create synastry or transit chart using the correct Kerykeion format
            if is_transit_chart:
                # Create transit chart (natal chart with transiting planets)
                chart_svg = KerykeionChartSVG(
                    first_subject,
                    "Transit", 
                    second_subject,
                    new_output_directory=temp_dir,
                    theme="dark",
                    active_points=active_points
                )
                print(f"DEBUG: Created transit chart with natal vs transits", file=sys.stderr)
            elif is_transit:
                # Legacy date-only transit (should not be used anymore)
                chart_svg = NoHousesChartSVG(
                    first_subject,
                    "Synastry",
                    second_subject,
                    new_output_directory=temp_dir,
                    theme="dark",
                    active_points=active_points,
                    _skip_houses=True
                )
            else:
                # Regular synastry chart
                chart_svg = KerykeionChartSVG(
                    first_subject,
                    "Synastry",
                    second_subject,
                    new_output_directory=temp_dir,
                    theme="dark",
                    active_points=active_points
                )
        elif is_transit:
            # Create pure transit chart - date only, no time or location needed
            # Use noon UTC at Greenwich for consistent planetary positions
            transit_params = {
                'name': birth_info['name'] + " (Transit)",
                'year': birth_info['year'],
                'month': birth_info['month'],
                'day': birth_info['day'],
                'hour': 12,  # Always noon for date-only transits
                'minute': 0,  # Always :00 for date-only transits
                'lng': 0.0,  # Greenwich longitude
                'lat': 51.5,  # Greenwich latitude  
                'tz_str': "UTC",  # Always UTC for pure transits
                'city': "Greenwich",
                'houses_system_identifier': 'P',  # Will be ignored for transit-only chart
                'zodiac_type': zodiac_type,
                'disable_chiron': True
            }
            if sidereal_mode:
                transit_params['sidereal_mode'] = sidereal_mode
                
            transit_subject = TransitSubject(**transit_params, _is_transit=True)
            
            # Wipe house data so chart drawer has nothing to render
            transit_subject.houses_list = []
            transit_subject.houses_dict = {}
            if hasattr(transit_subject, "cusps"):
                transit_subject.cusps = []
            if hasattr(transit_subject, "house_cusps"):
                transit_subject.house_cusps = []
            if hasattr(transit_subject, "house_cusps_list"):
                transit_subject.house_cusps_list = []
            if hasattr(transit_subject, 'houses'):
                transit_subject.houses = {}
            if hasattr(transit_subject, '_houses'):
                transit_subject._houses = {}
            if hasattr(transit_subject, '_house_cusps'):
                transit_subject._house_cusps = []
            if hasattr(transit_subject, '_cusps'):
                transit_subject._cusps = []
            if hasattr(transit_subject, 'house_positions'):
                transit_subject.house_positions = []
            
            # Log debug info for transit chart
            print(f"DEBUG: Creating transit chart with active_points: {active_points}", file=sys.stderr)
            print(f"DEBUG: Cleared all house data for transit chart", file=sys.stderr)
            
            # Create transit chart with planets only (no houses displayed)
            chart_svg = NoHousesChartSVG(
                transit_subject,
                new_output_directory=temp_dir,
                theme="dark",
                active_points=active_points,
                _skip_houses=True
            )
        else:
            # For regular charts (not transit), check if it's date-only
            if is_transit:
                chart_svg = NoHousesChartSVG(
                    first_subject,
                    new_output_directory=temp_dir,
                    theme="dark",
                    active_points=active_points,
                    _skip_houses=True
                )
            else:
                chart_svg = KerykeionChartSVG(
                    first_subject,
                    new_output_directory=temp_dir,
                    theme="dark",
                    active_points=active_points
                )

        # For transit/date-only charts, clear houses from the chart_svg object too
        if is_transit:
            # Clear houses from the subject(s) in the chart object
            if hasattr(chart_svg, 'first_subject'):
                chart_svg.first_subject.houses_list = []
                if hasattr(chart_svg.first_subject, 'houses'):
                    chart_svg.first_subject.houses = {}
            if hasattr(chart_svg, 'subject'):
                chart_svg.subject.houses_list = []
                if hasattr(chart_svg.subject, 'houses'):
                    chart_svg.subject.houses = {}
            # Clear any cached house data in the chart object itself
            if hasattr(chart_svg, 'houses_list'):
                chart_svg.houses_list = []
            if hasattr(chart_svg, '_houses_list'):
                chart_svg._houses_list = []
            print(f"DEBUG: Cleared houses from chart_svg object before rendering", file=sys.stderr)
        
        import io, contextlib, glob
        with io.StringIO() as buf, contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            try:
                # Try with remove_css_variables
                chart_svg.makeWheelOnlySVG(remove_css_variables=True)
            except TypeError:
                chart_svg.makeWheelOnlySVG()

        # Locate the generated SVG file in temp_dir
        svg_files = glob.glob(os.path.join(temp_dir, "*.svg"))
        if not svg_files:
            raise FileNotFoundError(f"No SVG file generated in {temp_dir}")

        svg_file = max(svg_files, key=os.path.getctime)
        with open(svg_file, "r", encoding="utf-8") as f:
            svg_content = f.read()

        if not svg_content or "<svg" not in svg_content:
            raise ValueError("Generated SVG file is empty or invalid")

        # Restore any monkeypatched methods if this was a transit chart
        if is_transit and original_methods:
            for method_name, original_method in original_methods.items():
                setattr(KerykeionChartSVG, method_name, original_method)
                
        # As a final fallback, aggressively remove any remaining house-like elements from SVG
        if is_transit:
            svg_content = aggressive_house_removal(svg_content)

        return svg_content.strip()


def aggressive_house_removal(svg_content: str) -> str:
    """Aggressively remove any lines that could be house divisions."""
    import re
    
    # Split SVG into lines for processing
    lines = svg_content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip lines that look like house division lines (straight lines from center)
        # Common patterns: lines with stroke attributes that go from center to edge
        if '<line' in line:
            # Skip thin lines (likely house divisions)
            if any(pattern in line for pattern in ['stroke-width="1"', 'stroke-width="0.5"', 'stroke-width="2"']):
                continue
            # Skip lines with gray/dark colors (common for house lines)
            if any(color in line.lower() for color in ['#666', '#777', '#888', '#999', '#aaa', '#bbb', '#ccc', 'gray', 'grey']):
                continue
                
        # Skip text elements with house numbers (1-12 or Roman numerals)
        if '<text' in line:
            if any(f'>{num}<' in line for num in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']):
                continue
            if any(f'>{roman}<' in line for roman in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']):
                continue
                
        # Keep all other lines
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def remove_house_elements_from_svg(svg_content: str) -> str:
    """Remove house lines and house numbers from SVG content."""
    import re
    
    # First, try to remove entire house groups if they exist
    svg_content = re.sub(r'<g[^>]*id="houses"[^>]*>.*?</g>', '', svg_content, flags=re.IGNORECASE | re.DOTALL)
    svg_content = re.sub(r'<g[^>]*houses[^>]*>.*?</g>', '', svg_content, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove house cusp lines (lines that radiate from center)
    # More general pattern that works with any chart center coordinates
    svg_content = re.sub(r'<line[^>]*(x1|y1)="[0-9]+"[^>]*>', '', svg_content)
    svg_content = re.sub(r'<line[^>]*stroke[^>]*(x1|y1)="[0-9]+"[^>]*>', '', svg_content)
    
    # Remove house numbers (text elements with numbers 1-12)
    for house_num in range(1, 13):
        # Match various text element patterns for house numbers
        svg_content = re.sub(f'<text[^>]*>\\s*{house_num}\\s*</text>', '', svg_content)
        svg_content = re.sub(f'<text[^>]*font[^>]*>\\s*{house_num}\\s*</text>', '', svg_content)
        # Roman numerals too (I, II, III, etc.)
        roman_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
        if house_num <= len(roman_numerals):
            roman = roman_numerals[house_num - 1]
            svg_content = re.sub(f'<text[^>]*>\\s*{roman}\\s*</text>', '', svg_content)
    
    # Remove any paths or elements with "house" in class or id
    svg_content = re.sub(r'<path[^>]*house[^>]*>', '', svg_content, flags=re.IGNORECASE)
    svg_content = re.sub(r'<circle[^>]*house[^>]*>', '', svg_content, flags=re.IGNORECASE)
    
    # Remove thin lines that typically represent house divisions
    # These often have stroke-width="1" or similar thin strokes
    svg_content = re.sub(r'<line[^>]*stroke-width="[0-2]"[^>]*>', '', svg_content)
    
    # Remove any remaining house division elements by common stroke colors
    # House lines are often gray or dark colors
    svg_content = re.sub(r'<line[^>]*stroke="#(?:666|777|888|999|aaa|bbb|ccc)"[^>]*>', '', svg_content, flags=re.IGNORECASE)
    
    return svg_content


def main():
    try:
        input_data = json.loads(sys.stdin.read())
        svg_content = generate_chart(input_data)
        print(svg_content)  # Only clean SVG to stdout
        sys.stdout.flush()
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()

        error_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400">
            <circle cx="200" cy="200" r="180" fill="none" stroke="#666" stroke-width="2"/>
            <text x="200" y="180" text-anchor="middle" font-family="Arial" font-size="16" fill="#666">
                Chart Generation Error
            </text>
            <text x="200" y="220" text-anchor="middle" font-family="Arial" font-size="12" fill="#999">
                {str(e)[:50]}
            </text>
        </svg>'''
        print(error_svg)
        sys.stdout.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()