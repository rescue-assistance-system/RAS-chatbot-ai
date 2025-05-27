import math
from supabase import create_client
from services.supabase_client import supabase


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_nearest_rescue_team(lat, lon, max_distance_km=50):
    # Step 1 : Query the rescue_teams table for active teams
    response = (
        supabase.table("rescue_teams")
        .select("id, user_id, team_name, status, default_latitude, default_longitude")
        .eq("is_active", True)
        .eq("status", "available")
        .execute()
    )
    print("Response from rescue_teams:", response)

    rescue_teams = response.data

    if not rescue_teams:
        return []

    nearest_teams = []
    for team in rescue_teams:
        team_lat = float(team["default_latitude"] or 0)
        team_lon = float(team["default_longitude"] or 0)
        distance = haversine(lat, lon, team_lat, team_lon)

        # Step 2: Query the accounts_ras_sys table to get phone numbers
        account_resp = (
            supabase.table("accounts_ras_sys")
            .select("phone")
            .eq("id", team["user_id"])
            .single()
            .execute()
        )

        phone = account_resp.data.get("phone") if account_resp.data else None

        if distance <= max_distance_km:
            nearest_teams.append(
                {
                    "team_name": team["team_name"],
                    "phone": phone,
                    "latitude": team_lat,
                    "longitude": team_lon,
                    "status": team["status"],
                    "distance_km": round(distance, 2),
                }
            )

    # Step 3: Sort teams by distance
    nearest_teams.sort(key=lambda t: t["distance_km"])

    return nearest_teams[:3]


def format_rescue_teams_text(teams):
    if not teams:
        return (
            "There are currently no rescue teams near you within the specified range."
        )

    response_lines = [f"There are {len(teams)} rescue teams near you:\n"]
    for i, team in enumerate(teams, 1):
        response_lines.append(
            f"{i}. {team['team_name']}\n"
            f"   - Phone: {team['phone']}\n"
            f"   - Distance: {team['distance_km']} km\n"
        )
    response_lines.append("Please contact the nearest team for timely assistance.")
    return "\n".join(response_lines)
