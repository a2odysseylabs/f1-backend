# F1nsight Backend API

FastAPI backend for Formula 1 data analysis using FastF1 and Ergast API.

## Setup and Run

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the application:**
    ```bash
    python -m uvicorn app.main:app --reload
    ```
    The API will be available at `http://localhost:8000`.

## API Endpoints

The base URL for all v1 endpoints is `/api/v1`.

### Schedule

-   **GET `/schedule/`**
    -   Description: Get the complete event schedule for a given year.
    -   Query Parameters:
        -   `year` (int, required): Season year (e.g., 2024).
        -   `include_testing` (bool, optional, default: False): Include pre-season testing events.
    -   Response Format: `List[ScheduleResponse]`
        ```json
        [
          {
            "round_number": 1,
            "event_name": "Bahrain Grand Prix",
            "event_date": "2024-03-02T18:00:00",
            "event_format": "conventional",
            "session1_date": "2024-02-29T14:30:00", // FP1
            "session2_date": "2024-02-29T18:00:00", // FP2
            "session3_date": "2024-03-01T15:30:00", // FP3
            "session4_date": "2024-03-01T19:00:00", // Qualifying
            "session5_date": "2024-03-02T18:00:00", // Race
            "f1_api_support": true,
            "location": "Sakhir",
            "country": "Bahrain"
          }
          // ... more events
        ]
        ```

-   **GET `/schedule/{year}/event/{event_identifier}`**
    -   Description: Get detailed information about a specific event.
    -   Path Parameters:
        -   `year` (int, required): Season year.
        -   `event_identifier` (Union[int, str], required): Event round number or name.
    -   Response Format: `EventResponse`
        ```json
        {
          "round_number": 1,
          "event_name": "Bahrain Grand Prix",
          "event_date": "2024-03-02T18:00:00",
          "event_format": "conventional",
          "location": "Sakhir",
          "country": "Bahrain",
          "f1_api_support": true,
          "sessions": [
            {"session_name": "Session1", "session_date": "2024-02-29T14:30:00"},
            {"session_name": "Session2", "session_date": "2024-02-29T18:00:00"},
            {"session_name": "Session3", "session_date": "2024-03-01T15:30:00"},
            {"session_name": "Session4", "session_date": "2024-03-01T19:00:00"},
            {"session_name": "Session5", "session_date": "2024-03-02T18:00:00"}
          ]
        }
        ```

-   **GET `/schedule/current`**
    -   Description: Get the current season schedule.
    -   Query Parameters:
        -   `include_testing` (bool, optional, default: False): Include pre-season testing events.
    -   Response Format: `List[ScheduleResponse]` (Same as `/schedule/`)

### Drivers

-   **GET `/drivers/`**
    -   Description: Get all drivers for a specific season.
    -   Query Parameters:
        -   `year` (int, required): Season year.
        -   `constructor` (str, optional): Filter by constructor ID (e.g., 'mercedes').
    -   Response Format: `List[DriverResponse]`
        ```json
        [
          {
            "driver_id": "hamilton",
            "driver_number": 44,
            "driver_code": "HAM",
            "given_name": "Lewis",
            "family_name": "Hamilton",
            "date_of_birth": "1985-01-07",
            "nationality": "British",
            "driver_url": "http://en.wikipedia.org/wiki/Lewis_Hamilton"
          }
          // ... more drivers
        ]
        ```

-   **GET `/drivers/{driver_id}/info`**
    -   Description: Get detailed information about a specific driver.
    -   Path Parameters:
        -   `driver_id` (str, required): Driver identifier (e.g., 'hamilton').
    -   Query Parameters:
        -   `year` (int, optional): Season year for context.
    -   Response Format: `DriverResponse` (Same as individual driver object above)

-   **GET `/drivers/session/{year}/{event}/{session}`**
    -   Description: Get drivers who participated in a specific session.
    -   Path Parameters:
        -   `year` (int, required): Season year.
        -   `event` (str, required): Event name or round number.
        -   `session` (str, required): Session type (R, Q, S, FP1, FP2, FP3).
    -   Response Format: `List[DriverSessionResponse]`
        ```json
        [
          {
            "driver_abbreviation": "HAM",
            "driver_number": 44,
            "given_name": "Lewis",
            "family_name": "Hamilton",
            "team_name": "Mercedes",
            "team_color": "00D2BE"
          }
          // ... more drivers in session
        ]
        ```

-   **GET `/drivers/standings/{year}`**
    -   Description: Get driver championship standings for a season.
    -   Path Parameters:
        -   `year` (int, required): Season year.
    -   Query Parameters:
        -   `round_number` (int, optional): Specific round number for standings.
    -   Response Format: `List[DriverStandingsResponse]`
        ```json
        [
          {
            "position": 1,
            "points": 413,
            "wins": 11,
            "driver_id": "verstappen",
            "driver_code": "VER",
            "given_name": "Max",
            "family_name": "Verstappen",
            "nationality": "Dutch"
          }
          // ... more standings
        ]
        ```

-   **GET `/drivers/current`**
    -   Description: Get current season drivers.
    -   Query Parameters:
        -   `constructor` (str, optional): Filter by constructor ID.
    -   Response Format: `List[DriverResponse]` (Same as `/drivers/`)

### Constructors

-   **GET `/constructors/`**
    -   Description: Get all constructors/teams for a specific season.
    -   Query Parameters:
        -   `year` (int, required): Season year.
    -   Response Format: `List[ConstructorResponse]`
        ```json
        [
          {
            "constructor_id": "mercedes",
            "constructor_name": "Mercedes",
            "nationality": "German",
            "constructor_url": "http://en.wikipedia.org/wiki/Mercedes-Benz_in_Formula_One"
          }
          // ... more constructors
        ]
        ```

-   **GET `/constructors/{constructor_id}/info`**
    -   Description: Get detailed information about a specific constructor.
    -   Path Parameters:
        -   `constructor_id` (str, required): Constructor identifier (e.g., 'mercedes').
    -   Query Parameters:
        -   `year` (int, optional): Season year for context.
    -   Response Format: `ConstructorResponse` (Same as individual constructor object above)

-   **GET `/constructors/standings/{year}`**
    -   Description: Get constructor championship standings for a season.
    -   Path Parameters:
        -   `year` (int, required): Season year.
    -   Query Parameters:
        -   `round_number` (int, optional): Specific round number for standings.
    -   Response Format: `List[ConstructorStandingsResponse]`
        ```json
        [
          {
            "position": 1,
            "points": 650,
            "wins": 15,
            "constructor_id": "red_bull",
            "constructor_name": "Red Bull",
            "nationality": "Austrian"
          }
          // ... more standings
        ]
        ```

-   **GET `/constructors/{constructor_id}/drivers/{year}`**
    -   Description: Get all drivers for a specific constructor in a given year.
    -   Path Parameters:
        -   `constructor_id` (str, required): Constructor identifier.
        -   `year` (int, required): Season year.
    -   Response Format: `List[DriverResponse]` (Simplified, without URL and DOB)
        ```json
        [
          {
            "driver_id": "hamilton",
            "driver_number": 44,
            "driver_code": "HAM",
            "given_name": "Lewis",
            "family_name": "Hamilton",
            "nationality": "British"
          }
          // ... more drivers for the constructor
        ]
        ```

-   **GET `/constructors/current`**
    -   Description: Get current season constructors.
    -   Response Format: `List[ConstructorResponse]` (Same as `/constructors/`)

-   **GET `/constructors/seasons`**
    -   Description: Get all seasons a constructor participated in. (Simplified placeholder)
    -   Query Parameters:
        -   `constructor_id` (str, required): Constructor identifier.
    -   Response Format: `List[dict]`
        ```json
        [
            {"message": "Constructor red_bull found. Season details would be implemented with more complex queries."}
        ]
        ```

### Results

-   **GET `/results/race/{year}`**
    -   Description: Get race results for a season or specific race.
    -   Path Parameters:
        -   `year` (int, required): Season year.
    -   Query Parameters:
        -   `round_number` (int, optional): Specific round number.
        -   `driver` (str, optional): Filter by driver ID.
        -   `constructor` (str, optional): Filter by constructor ID.
    -   Response Format: `List[RaceResultResponse]`
        ```json
        [
          {
            "season": 2023,
            "round": 1,
            "race_name": "Bahrain Grand Prix",
            "circuit_name": "Bahrain International Circuit",
            "race_date": "2023-03-05",
            "position": 1,
            "position_text": "1",
            "points": 25,
            "driver_id": "verstappen",
            "driver_code": "VER",
            "driver_number": 1,
            "given_name": "Max",
            "family_name": "Verstappen",
            "constructor_id": "red_bull",
            "constructor_name": "Red Bull",
            "grid_position": 1,
            "laps_completed": 57,
            "status": "Finished",
            "fastest_lap_rank": 2,
            "fastest_lap_time": "1:33.996"
          }
          // ... more results
        ]
        ```

-   **GET `/results/qualifying/{year}`**
    -   Description: Get qualifying results for a season or specific race.
    -   Path Parameters:
        -   `year` (int, required): Season year.
    -   Query Parameters:
        -   `round_number` (int, optional): Specific round number.
        -   `driver` (str, optional): Filter by driver ID.
        -   `constructor` (str, optional): Filter by constructor ID.
    -   Response Format: `List[QualifyingResultResponse]`
        ```json
        [
          {
            "season": 2023,
            "round": 1,
            "race_name": "Bahrain Grand Prix",
            "circuit_name": "Bahrain International Circuit",
            "race_date": "2023-03-04", // Date of qualifying
            "position": 1,
            "driver_id": "verstappen",
            "driver_code": "VER",
            "driver_number": 1,
            "given_name": "Max",
            "family_name": "Verstappen",
            "constructor_id": "red_bull",
            "constructor_name": "Red Bull",
            "q1_time": "1:31.295",
            "q2_time": "1:30.503",
            "q3_time": "1:29.708"
          }
          // ... more results
        ]
        ```

-   **GET `/results/sprint/{year}`**
    -   Description: Get sprint race results for a season or specific race.
    -   Path Parameters:
        -   `year` (int, required): Season year.
    -   Query Parameters:
        -   `round_number` (int, optional): Specific round number.
        -   `driver` (str, optional): Filter by driver ID.
        -   `constructor` (str, optional): Filter by constructor ID.
    -   Response Format: `List[SprintResultResponse]`
        ```json
        [
          {
            "season": 2023,
            "round": 4, // Example round with a sprint
            "race_name": "Azerbaijan Grand Prix",
            "circuit_name": "Baku City Circuit",
            "race_date": "2023-04-29", // Date of sprint
            "position": 1,
            "position_text": "1",
            "points": 8,
            "driver_id": "perez",
            "driver_code": "PER",
            "driver_number": 11,
            "given_name": "Sergio",
            "family_name": "Pérez",
            "constructor_id": "red_bull",
            "constructor_name": "Red Bull",
            "grid_position": 2,
            "laps_completed": 17,
            "status": "Finished"
          }
          // ... more results
        ]
        ```

-   **GET `/results/session/{year}/{event}/{session}`**
    -   Description: Get results from a specific session using FastF1.
    -   Path Parameters:
        -   `year` (int, required): Season year.
        -   `event` (str, required): Event name or round number.
        -   `session` (str, required): Session type (R, Q, S, FP1, FP2, FP3).
    -   Response Format: `FullSessionResultsResponse`
        ```json
        {
          "session_info": {
            "year": 2023,
            "event": "Bahrain Grand Prix",
            "session": "R",
            "session_name": "Race",
            "date": "2023-03-05T15:00:00"
          },
          "results": [
            {
              "position": 1,
              "driver_number": 1,
              "driver_abbreviation": "VER",
              "driver_name": "Max Verstappen",
              "team_name": "Red Bull Racing",
              "time": "1:33:56.736", // Or other relevant session data like lap time for FP/Q
              "status": "Finished",
              "points": 25
            }
            // ... more session results
          ]
        }
        ```

-   **GET `/results/current/race`**
    -   Description: Get current season race results.
    -   Query Parameters:
        -   `round_number` (int, optional): Specific round number.
    -   Response Format: `List[RaceResultResponse]` (Same as `/results/race/{year}`)

-   **GET `/results/current/qualifying`**
    -   Description: Get current season qualifying results.
    -   Query Parameters:
        -   `round_number` (int, optional): Specific round number.
    -   Response Format: `List[QualifyingResultResponse]` (Same as `/results/qualifying/{year}`)

### Telemetry

**NEW!** Comprehensive telemetry endpoints providing detailed car performance data including speed, RPM, throttle, brake, DRS, steering, position coordinates, and advanced analytics.

-   **GET `/telemetry/session/{year}/{event}/{session}`**
    -   Description: Get comprehensive telemetry data for all drivers in a session.
    -   Path Parameters:
        -   `year` (int, required): Season year.
        -   `event` (str, required): Event name or round number.
        -   `session` (str, required): Session type (R, Q, S, FP1, FP2, FP3).
    -   Query Parameters:
        -   `drivers` (str, optional): Comma-separated driver abbreviations (e.g., 'VER,HAM').
        -   `laps` (str, optional): Comma-separated lap numbers (e.g., '1,5,10').
        -   `max_laps_per_driver` (int, optional, default: 5): Maximum laps per driver to return.
    -   Response Format: `SessionTelemetryResponse`
        ```json
        {
          "session_info": {
            "year": 2023,
            "event": "Bahrain Grand Prix",
            "session_type": "R",
            "track_name": "Bahrain Grand Prix",
            "country": "Bahrain",
            "date": "2023-03-05T15:00:00",
            "total_laps": 1150
          },
          "drivers": ["VER", "HAM", "PER"],
          "laps": [
            {
              "driver": "VER",
              "lap_number": 1,
              "lap_time": 95.234,
              "is_accurate": true,
              "max_speed": 315.2,
              "avg_speed": 185.6,
              "max_rpm": 11800,
              "avg_rpm": 8950.5,
              "throttle_percentage": 68.5,
              "brake_percentage": 15.2,
              "drs_percentage": 22.8,
              "gear_changes": 24,
              "telemetry_points": [
                {
                  "time": 1234.567,
                  "distance": 0.0,
                  "x": 1234.56,
                  "y": 2345.67,
                  "z": 12.34,
                  "speed": 285.4,
                  "rpm": 11500,
                  "n_gear": 7,
                  "throttle": 95.2,
                  "brake": false,
                  "drs": 1,
                  "steering": -12.5
                }
                // ... more telemetry points throughout the lap
              ]
            }
          ]
        }
        ```

-   **GET `/telemetry/lap/{year}/{event}/{session}/{driver}/{lap_number}`**
    -   Description: Get detailed telemetry data for a specific lap.
    -   Path Parameters:
        -   `year` (int, required): Season year.
        -   `event` (str, required): Event name or round number.
        -   `session` (str, required): Session type.
        -   `driver` (str, required): Driver abbreviation (e.g., 'VER').
        -   `lap_number` (int, required): Specific lap number.
    -   Response Format: `LapTelemetryResponse`
        ```json
        {
          "driver": "VER",
          "lap_number": 15,
          "lap_time": 93.459,
          "is_accurate": true,
          "max_speed": 318.7,
          "avg_speed": 189.3,
          "max_rpm": 11950,
          "avg_rpm": 9150.2,
          "throttle_percentage": 71.8,
          "brake_percentage": 14.6,
          "drs_percentage": 25.3,
          "gear_changes": 26,
          "telemetry_points": [
            // Detailed telemetry data points with coordinates, speeds, etc.
          ]
        }
        ```

-   **GET `/telemetry/compare/{year}/{event}/{session}`**
    -   Description: Compare telemetry data between two drivers.
    -   Path Parameters:
        -   `year` (int, required): Season year.
        -   `event` (str, required): Event name or round number.
        -   `session` (str, required): Session type.
    -   Query Parameters:
        -   `driver1` (str, required): First driver abbreviation.
        -   `driver2` (str, required): Second driver abbreviation.
        -   `lap_type` (str, optional, default: "fastest"): Lap type (fastest, first, last, specific).
        -   `lap1` (int, optional): Specific lap number for driver 1 (if lap_type is 'specific').
        -   `lap2` (int, optional): Specific lap number for driver 2 (if lap_type is 'specific').
    -   Response Format: `DriverComparisonResponse`
        ```json
        {
          "driver_1": "VER",
          "driver_2": "HAM",
          "lap_1": {
            // Complete lap telemetry for driver 1
          },
          "lap_2": {
            // Complete lap telemetry for driver 2
          },
          "comparison_stats": {
            "time_difference": -0.284,
            "speed_difference": {
              "max_speed_diff": 2.3,
              "avg_speed_diff": 1.7
            },
            "driving_style": {
              "throttle_diff": 3.2,
              "brake_usage_diff": -1.8,
              "drs_usage_diff": 2.1
            }
          }
        }
        ```

-   **GET `/telemetry/summary/{year}/{event}/{session}/{driver}`**
    -   Description: Get comprehensive telemetry summary for a driver in a session.
    -   Path Parameters:
        -   `year` (int, required): Season year.
        -   `event` (str, required): Event name or round number.
        -   `session` (str, required): Session type.
        -   `driver` (str, required): Driver abbreviation.
    -   Response Format: `TelemetrySummaryResponse`
        ```json
        {
          "driver": "VER",
          "session_type": "R",
          "total_laps": 57,
          "fastest_lap": {
            // Complete fastest lap telemetry data
          },
          "session_max_speed": 324.5,
          "session_avg_speed": 187.8,
          "session_max_rpm": 12000,
          "total_distance": 308550.0,
          "avg_throttle_usage": 69.3,
          "avg_brake_usage": 16.7,
          "aggressive_braking_count": 12,
          "drs_usage_percentage": 23.8,
          "gear_change_frequency": 25.4
        }
        ```

-   **GET `/telemetry/fastest-lap/{year}/{event}/{session}`**
    -   Description: Get telemetry data for the fastest laps in a session.
    -   Path Parameters:
        -   `year` (int, required): Season year.
        -   `event` (str, required): Event name or round number.
        -   `session` (str, required): Session type.
    -   Query Parameters:
        -   `limit` (int, optional, default: 10): Number of fastest laps to return.
    -   Response Format: `List[LapTelemetryResponse]`
        ```json
        [
          {
            "driver": "VER",
            "lap_number": 42,
            "lap_time": 92.681,
            // ... complete telemetry data for fastest lap
          },
          {
            "driver": "HAM",
            "lap_number": 38,
            "lap_time": 92.947,
            // ... complete telemetry data for second fastest lap
          }
          // ... more fastest laps
        ]
        ```

-   **GET `/telemetry/stint/{year}/{event}/{session}/{driver}`**
    -   Description: Get telemetry data organized by tire stints for a driver.
    -   Path Parameters:
        -   `year` (int, required): Season year.
        -   `event` (str, required): Event name or round number.
        -   `session` (str, required): Session type.
        -   `driver` (str, required): Driver abbreviation.
    -   Response Format: `List[StintTelemetryResponse]`
        ```json
        [
          {
            "driver": "VER",
            "stint_number": 1,
            "start_lap": 1,
            "end_lap": 18,
            "tire_compound": "MEDIUM",
            "tire_age": 18,
            "avg_lap_time": 94.235,
            "fastest_lap_time": 93.124,
            "tire_degradation": 0.025,
            "avg_speed": 186.4,
            "avg_throttle": 68.9,
            "avg_brake_usage": 17.2,
            "stint_laps": [
              // Complete telemetry for each lap in the stint
            ]
          }
          // ... more stints
        ]
        ```

-   **GET `/telemetry/track-analysis/{year}/{event}`**
    -   Description: Get track analysis based on telemetry data from all drivers.
    -   Path Parameters:
        -   `year` (int, required): Season year.
        -   `event` (str, required): Event name or round number.
    -   Query Parameters:
        -   `session` (str, optional, default: "R"): Session type for analysis.
    -   Response Format: `TrackDataResponse`
        ```json
        {
          "track_name": "Bahrain Grand Prix",
          "track_length": 5412.0,
          "corner_count": 14,
          "speed_zones": [
            {
              "zone_number": 1,
              "start_distance": 0.0,
              "end_distance": 270.6,
              "zone_type": "high_speed",
              "avg_speed": 285.4,
              "max_speed": 324.5
            }
            // ... more speed zones
          ],
          "braking_zones": [
            {
              "zone_number": 1,
              "start_distance": 240.0,
              "end_distance": 290.0,
              "brake_intensity": 85.6,
              "avg_speed": 125.3
            }
            // ... more braking zones
          ],
          "drs_zones": [
            {
              "zone_number": 1,
              "start_distance": 4800.0,
              "end_distance": 5200.0,
              "drs_usage": 95.2,
              "avg_speed": 298.7
            }
            // ... more DRS zones
          ]
        }
        ```

## Pydantic Models

Response models are defined in the `app/models/` directory.

-   `schedule.py`: `ScheduleResponse`, `EventResponse`, `SessionInfo`
-   `drivers.py`: `DriverResponse`, `DriverSessionResponse`, `DriverStandingsResponse`
-   `constructors.py`: `ConstructorResponse`, `ConstructorStandingsResponse`
-   `results.py`: `RaceResultResponse`, `QualifyingResultResponse`, `SprintResultResponse`, `SessionResultResponse`, `FullSessionResultsResponse`
-   `telemetry.py`: `TelemetryPoint`, `LapTelemetryResponse`, `SessionTelemetryResponse`, `DriverComparisonResponse`, `TelemetrySummaryResponse`, `TrackDataResponse`, `StintTelemetryResponse`

Each model defines the expected structure of the API response for the corresponding endpoint.

## Telemetry Data Features

The telemetry endpoints provide comprehensive F1 car performance data:

### Available Telemetry Data
- **Position**: X, Y, Z coordinates on track
- **Speed**: Real-time speed in km/h
- **Engine**: RPM, throttle position (0-100%)
- **Brakes**: Brake status and intensity
- **Transmission**: Current gear, gear changes
- **Aerodynamics**: DRS status and usage
- **Control**: Steering wheel angle
- **Time**: Session time and lap distance

### Advanced Analytics
- **Lap Statistics**: Max/avg speed, RPM, throttle/brake/DRS usage percentages
- **Driver Comparison**: Side-by-side telemetry analysis with performance differences
- **Stint Analysis**: Tire compound performance and degradation tracking
- **Track Analysis**: Speed zones, braking points, and DRS zones identification
- **Session Summaries**: Comprehensive driver performance metrics

### Use Cases
- **Performance Analysis**: Compare driver techniques and car performance
- **Strategy Insights**: Analyze tire strategies and pit stop timing
- **Track Characteristics**: Understand circuit-specific challenges
- **Driver Development**: Identify areas for improvement
- **Race Engineering**: Optimize car setup and race strategy

All telemetry data is sourced from FastF1 and provides the same level of detail used by F1 teams for analysis. 