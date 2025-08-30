#!/usr/bin/env python3
"""
Dynamic Natal Chart Generator using Kerykeion
Properly configured for Lucy bot's three data sources with wheel-only SVG charts.
Supports: user_profiles, idols, charts tables with dynamic chart preferences.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any
import urllib.request
import urllib.parse
import urllib.error

# Import Kerykeion library and configure Swiss Ephemeris path
try:
    from kerykeion import AstrologicalSubject, KerykeionChartSVG
    from kerykeion.kr_types import ChartType
    import swisseph as swe
    
    # Configure Swiss Ephemeris path for Kerykeion
    ephemeris_path = os.environ.get('SWISSEPH_PATH', '/usr/share/swisseph')
    swe.set_ephe_path(ephemeris_path)
    
    KERYKEION_AVAILABLE = True
    print(f"Kerykeion initialized with ephemeris path: {ephemeris_path}", file=sys.stderr)
except ImportError as e:
    print(f"Error: Kerykeion library not available: {e}", file=sys.stderr)
    KERYKEION_AVAILABLE = False

class DynamicNatalGenerator:
    """
    Dynamic chart generator using natal-0.9.4 with Swiss Ephemeris API integration.
    Handles all three Lucy bot data sources with proper user preferences.
    """
    
    def __init__(self, swiss_ephemeris_url: str = "http://astro-api.dsdn.synology.me"):
        self.swiss_ephemeris_url = swiss_ephemeris_url
    
    def generate_chart(self, chart_input: Dict[str, Any]) -> str:
        """
        Generate SVG chart from chart input data using Kerykeion.
        
        Args:
            chart_input: Contains chart data, preferences, and options
            
        Returns:
            SVG content as string
        """
        if not KERYKEION_AVAILABLE:
            return self._generate_error_svg("Kerykeion library not available")
        
        try:
            # Extract data based on source type
            source_type = chart_input.get('source_type', 'chart')
            
            # Handle synastry charts
            if source_type == 'synastry':
                return self._generate_synastry_chart(chart_input)
            
            # Handle single charts
            chart_data = self._extract_chart_data(chart_input, source_type)
            
            if not chart_data:
                return self._generate_error_svg("Invalid chart data")
            
            # Get options for chart generation
            options = chart_input.get('options', {})
            theme = options.get('theme', 'dark')
            
            # Create AstrologicalSubject
            subject = self._create_astrological_subject(chart_data)
            
            # Create chart SVG generator (minimal parameters)
            chart_svg = KerykeionChartSVG(subject)
            
            # Set up working directory for file generation
            import glob
            import os
            original_cwd = os.getcwd()
            
            # Use /tmp directory directly (most permissive)
            print(f"DEBUG: Current working directory before: {os.getcwd()}", file=sys.stderr)
            print(f"DEBUG: Changing to /tmp directory", file=sys.stderr)
            os.chdir("/tmp")
            print(f"DEBUG: Current working directory after: {os.getcwd()}", file=sys.stderr)
            print(f"DEBUG: /tmp permissions: {oct(os.stat('/tmp').st_mode)[-3:]}", file=sys.stderr)
            
            try:
                # Test if we can write to /tmp
                test_file = "/tmp/test_write_py.txt"
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                print(f"DEBUG: /tmp write test successful", file=sys.stderr)
                
                # Generate wheel-only SVG (creates file, doesn't return content)
                print(f"DEBUG: About to call makeWheelOnlySVG()", file=sys.stderr)
                chart_svg.makeWheelOnlySVG()
                print(f"DEBUG: makeWheelOnlySVG() completed", file=sys.stderr)
                
                # Find the generated SVG file in both /tmp and current directory
                svg_files = []
                svg_files.extend(glob.glob(os.path.join("/tmp", "*.svg")))
                svg_files.extend(glob.glob(os.path.join(os.getcwd(), "*.svg")))
                
                if svg_files:
                    # Read the most recently created SVG file
                    svg_file = max(svg_files, key=os.path.getctime)
                    with open(svg_file, 'r') as f:
                        svg_content = f.read()
                    
                    # Clean up the file
                    os.remove(svg_file)
                    
                    # Post-process for Discord display
                    return self._optimize_for_discord(svg_content, {}, options)
                else:
                    return self._generate_error_svg("Kerykeion failed to generate SVG file")
            finally:
                # Always restore original working directory
                os.chdir(original_cwd)
            
        except Exception as e:
            print(f"Chart generation error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            # Show more detailed error information
            error_details = f"{type(e).__name__}: {str(e)}"
            if hasattr(e, 'errno'):
                error_details += f" (errno: {e.errno})"
            if hasattr(e, 'filename') and e.filename:
                error_details += f" (file: {e.filename})"
            return self._generate_error_svg(f"Generation failed: {error_details}")
    
    def _extract_chart_data(self, chart_input: Dict[str, Any], source_type: str) -> Optional[Dict[str, Any]]:
        """
        Extract chart data from different Lucy bot data sources.
        """
        try:
            if source_type == 'user_profile':
                # From user_profiles table
                return {
                    'name': chart_input.get('name', 'Profile Chart'),
                    'birth_date': chart_input.get('chart_birth_date'),
                    'birth_time': chart_input.get('chart_birth_time', '12:00'),
                    'birth_city': chart_input.get('chart_birth_city'),
                    'birth_country': chart_input.get('chart_birth_country'),
                    'latitude': chart_input.get('chart_birth_latitude'),
                    'longitude': chart_input.get('chart_birth_longitude'),
                    'timezone': chart_input.get('chart_birth_timezone', 'UTC')
                }
            
            elif source_type == 'idol':
                # From idols table
                return {
                    'name': chart_input.get('name', 'Celebrity Chart'),
                    'birth_date': chart_input.get('birth_date'),
                    'birth_time': chart_input.get('birth_time', '12:00'),
                    'birth_city': chart_input.get('birth_city'),
                    'birth_country': chart_input.get('birth_country'),
                    'latitude': chart_input.get('birth_latitude'),
                    'longitude': chart_input.get('birth_longitude'),
                    'timezone': chart_input.get('birth_timezone', 'UTC')
                }
            
            elif source_type == 'chart':
                # From charts table
                return {
                    'name': chart_input.get('name', 'Saved Chart'),
                    'birth_date': chart_input.get('birth_date'),
                    'birth_time': chart_input.get('birth_time', '12:00'),
                    'birth_city': chart_input.get('birth_city'),
                    'birth_country': chart_input.get('birth_country'),
                    'latitude': chart_input.get('birth_latitude'),
                    'longitude': chart_input.get('birth_longitude'),
                    'timezone': chart_input.get('birth_timezone', 'UTC')
                }
            
            elif source_type == 'processed_chart_data':
                # From processed chart data (Swiss Ephemeris format)
                chart_data = chart_input.get('chart_data', {})
                return {
                    'name': chart_data.get('name', 'Processed Chart'),
                    'birth_date': chart_data.get('birth_date'),
                    'birth_time': chart_data.get('birth_time', '12:00'),
                    'birth_city': chart_data.get('birth_city'),
                    'birth_country': chart_data.get('birth_country'),
                    'latitude': chart_data.get('latitude'),
                    'longitude': chart_data.get('longitude'),
                    'timezone': chart_data.get('timezone', 'UTC')
                }
            
            else:
                # Generic chart data
                return chart_input.get('chart_data', {})
                
        except Exception as e:
            print(f"Error extracting chart data: {e}", file=sys.stderr)
            return None
    
    def _create_astrological_subject(self, chart_data: Dict[str, Any]):
        """
        Create Kerykeion AstrologicalSubject from chart data.
        """
        # Parse birth date and time
        birth_date_str = chart_data.get('birth_date')
        birth_time_str = chart_data.get('birth_time', '12:00:00')
        
        # Extract date components
        if isinstance(birth_date_str, str):
            if 'T' in birth_date_str:  # ISO format
                birth_datetime = datetime.fromisoformat(birth_date_str.replace('Z', '+00:00'))
            else:
                # Date only, add time
                birth_datetime = datetime.fromisoformat(f"{birth_date_str}T{birth_time_str}")
        else:
            # Fallback
            birth_datetime = datetime(1990, 1, 1, 12, 0)
        
        # Extract time components
        hour = birth_datetime.hour
        minute = birth_datetime.minute
        
        # Get location info
        city = chart_data.get('birth_city', 'London')
        country = chart_data.get('birth_country', 'GB')
        
        # Handle country code formatting
        if len(country) > 2:
            # Convert full country names to country codes
            country_mapping = {
                'United States': 'US',
                'United Kingdom': 'GB', 
                'Canada': 'CA',
                'Australia': 'AU',
                'Germany': 'DE',
                'France': 'FR',
                'Italy': 'IT',
                'Spain': 'ES',
                'Netherlands': 'NL',
                'Belgium': 'BE',
                'Switzerland': 'CH',
                'Austria': 'AT',
                'Japan': 'JP',
                'China': 'CN',
                'India': 'IN',
                'Brazil': 'BR',
                'Mexico': 'MX',
                'Argentina': 'AR',
                'Russia': 'RU',
                'Norway': 'NO',
                'Sweden': 'SE',
                'Denmark': 'DK',
                'Finland': 'FI'
            }
            country = country_mapping.get(country, 'GB')
        
        # Create AstrologicalSubject
        subject = AstrologicalSubject(
            name=chart_data.get('name', 'Chart'),
            year=birth_datetime.year,
            month=birth_datetime.month,
            day=birth_datetime.day,
            hour=hour,
            minute=minute,
            city=city,
            nation=country
        )
        
        return subject
    
    def _get_chart_width(self, size: str) -> int:
        """
        Get chart width based on size preference - large square images.
        """
        size_mapping = {
            'small': 600,
            'medium': 800,
            'large': 1200  # Large square for better visibility
        }
        return size_mapping.get(size, 1200)
    
    def _optimize_for_discord(self, svg_content: str, preferences: Dict[str, Any], 
                            options: Dict[str, Any]) -> str:
        """
        Optimize SVG for Discord display - clean circular chart only.
        """
        try:
            # Ensure proper SVG namespace
            if 'xmlns="http://www.w3.org/2000/svg"' not in svg_content:
                svg_content = svg_content.replace(
                    '<svg', 
                    '<svg xmlns="http://www.w3.org/2000/svg"', 
                    1
                )
            
            # Add viewBox if not present for proper scaling
            if 'viewBox=' not in svg_content:
                # Extract width and height if available
                import re
                width_match = re.search(r'width="(\d+)"', svg_content)
                height_match = re.search(r'height="(\d+)"', svg_content)
                
                if width_match and height_match:
                    width = width_match.group(1)
                    height = height_match.group(1)
                    svg_content = svg_content.replace(
                        '<svg',
                        f'<svg viewBox="0 0 {width} {height}"',
                        1
                    )
            
            return svg_content
            
        except Exception as e:
            print(f"Warning: SVG optimization failed: {e}", file=sys.stderr)
            return svg_content
    
    def _generate_error_svg(self, error_message: str) -> str:
        """
        Generate a clean error SVG for display.
        """
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
            <circle cx="200" cy="200" r="180" fill="none" stroke="#666" stroke-width="2"/>
            <text x="200" y="180" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" fill="#666">
                Chart Generation Error
            </text>
            <text x="200" y="220" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#999">
                {error_message[:50]}
            </text>
        </svg>'''

    def _generate_synastry_chart(self, chart_input: Dict[str, Any]) -> str:
        """
        Generate synastry chart using Kerykeion with two AstrologicalSubjects.
        """
        try:
            # Get both charts data
            primary_chart = chart_input.get('primary_chart')
            synastry_chart = chart_input.get('synastry_chart')
            
            if not primary_chart or not synastry_chart:
                return self._generate_error_svg("Missing synastry chart data")
            
            # Create first AstrologicalSubject
            first = self._create_astrological_subject_from_chart_data(primary_chart)
            
            # Create second AstrologicalSubject
            second = self._create_astrological_subject_from_chart_data(synastry_chart)
            
            # Create synastry chart using Kerykeion's synastry functionality
            synastry_chart_svg = KerykeionChartSVG(first, "Synastry", second)
            
            # Generate wheel-only synastry SVG
            # Set up working directory for file generation
            import glob
            import os
            original_cwd = os.getcwd()
            
            # Use /tmp directory directly (most permissive)
            os.chdir("/tmp")
            
            try:
                synastry_chart_svg.makeWheelOnlySVG()
                
                # Find the generated SVG file in both /tmp and current directory
                svg_files = []
                svg_files.extend(glob.glob(os.path.join("/tmp", "*.svg")))
                svg_files.extend(glob.glob(os.path.join(os.getcwd(), "*.svg")))
                
                if svg_files:
                    # Read the most recently created SVG file
                    svg_file = max(svg_files, key=os.path.getctime)
                    with open(svg_file, 'r') as f:
                        svg_content = f.read()
                    
                    # Clean up the file
                    os.remove(svg_file)
                    
                    # Post-process for Discord display
                    options = chart_input.get('options', {})
                    return self._optimize_for_discord(svg_content, {}, options)
                else:
                    return self._generate_error_svg("Kerykeion failed to generate synastry SVG file")
            finally:
                # Always restore original working directory
                os.chdir(original_cwd)
                
        except Exception as e:
            print(f"Synastry generation error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return self._generate_error_svg(f"Synastry generation failed: {str(e)}")

    def _create_astrological_subject_from_chart_data(self, chart_data: Dict[str, Any]) -> Any:
        """
        Create AstrologicalSubject from chart data dictionary.
        """
        # Parse birth date
        birth_date_str = chart_data.get('birth_date')
        if isinstance(birth_date_str, str):
            birth_datetime = datetime.fromisoformat(birth_date_str.replace('Z', '+00:00'))
        else:
            birth_datetime = datetime.now()
        
        # Parse birth time
        time_str = chart_data.get('birth_time', '12:00')
        time_parts = time_str.split(':')
        hour = int(time_parts[0]) if len(time_parts) > 0 else 12
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        
        # Get location data
        city = chart_data.get('birth_city', 'Unknown')
        country = chart_data.get('birth_country', 'US')
        
        # Map country names to ISO codes
        country_code = self._map_country_to_code(country)
        
        name = chart_data.get('name', 'Person')
        
        return AstrologicalSubject(
            name=name,
            year=birth_datetime.year,
            month=birth_datetime.month,
            day=birth_datetime.day,
            hour=hour,
            minute=minute,
            city=city,
            nation=country_code
        )

    def _map_country_to_code(self, country: str) -> str:
        """
        Map country names to ISO country codes for Kerykeion.
        """
        if not country or len(country) <= 2:
            return country or 'US'
        
        country_mapping = {
            'United States': 'US',
            'United Kingdom': 'GB', 
            'Canada': 'CA',
            'Australia': 'AU',
            'Germany': 'DE',
            'France': 'FR',
            'Italy': 'IT',
            'Spain': 'ES',
            'Netherlands': 'NL',
            'Belgium': 'BE',
            'Switzerland': 'CH',
            'Austria': 'AT',
            'Japan': 'JP',
            'China': 'CN',
            'India': 'IN',
            'Brazil': 'BR',
            'Mexico': 'MX',
            'Argentina': 'AR',
            'Russia': 'RU',
            'Norway': 'NO',
            'Sweden': 'SE',
            'Denmark': 'DK',
            'Finland': 'FI',
            'Poland': 'PL',
            'Czech Republic': 'CZ',
            'Hungary': 'HU',
            'Ireland': 'IE',
            'Portugal': 'PT',
            'Greece': 'GR',
            'Turkey': 'TR',
            'Israel': 'IL',
            'Egypt': 'EG',
            'South Africa': 'ZA',
            'New Zealand': 'NZ',
            'South Korea': 'KR',
            'Thailand': 'TH',
            'Singapore': 'SG',
            'Philippines': 'PH',
            'Malaysia': 'MY',
            'Indonesia': 'ID',
            'Vietnam': 'VN',
            'Chile': 'CL',
            'Colombia': 'CO',
            'Peru': 'PE',
            'Venezuela': 'VE',
            'Ukraine': 'UA',
            'Romania': 'RO',
            'Bulgaria': 'BG',
            'Croatia': 'HR',
            'Serbia': 'RS',
            'Slovenia': 'SI',
            'Slovakia': 'SK',
            'Lithuania': 'LT',
            'Latvia': 'LV',
            'Estonia': 'EE',
            'Iceland': 'IS',
            'Luxembourg': 'LU',
            'Malta': 'MT',
            'Cyprus': 'CY'
        }
        
        return country_mapping.get(country, 'US')


def main():
    """
    Main entry point - reads JSON from stdin, outputs SVG to stdout.
    """
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())
        
        # Create generator
        generator = DynamicNatalGenerator()
        
        # Generate chart SVG
        svg_content = generator.generate_chart(input_data)
        
        # Output SVG to stdout
        print(svg_content)
        
    except Exception as e:
        print(f"Fatal error in main: {e}", file=sys.stderr)
        # Output fallback SVG
        print('''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
            <circle cx="200" cy="200" r="180" fill="none" stroke="#ff4444" stroke-width="3"/>
            <text x="200" y="200" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" fill="#ff4444">
                Chart System Error
            </text>
        </svg>''')
        sys.exit(1)


if __name__ == "__main__":
    main()