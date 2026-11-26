import json
from pathlib import Path

DATA = Path(__file__).parent / "data"

with open(DATA / "days.json", encoding="utf-8") as f:
    DAYS = json.load(f)
with open(DATA / "questions.json", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

LEVELS = [
    {"value": "0", "label": "לא"},
    {"value": "1", "label": "קצת"},
    {"value": "2", "label": "מאוד"},
    {"value": "3", "label": "חובה"},
]

REGION_NAMES = {"tokyo": "טוקיו", "nagoya": "נגויה", "osaka": "אוסקה", "kobe": "קובה"}
KANSAI = {"nagoya", "osaka", "kobe"}

TAG_NAMES = {
    "food": "אוכל",
    "shopping": "קניות",
    "fashion": "סטריטוור",
    "cars": "רכבים",
    "culture": "מקדשים וטירות",
    "anime": "אנימה",
    "games": "גיימינג",
    "nightlife": "חיי לילה",
    "views": "תצפיות",
    "nature": "טבע",
    "sport": "סומו",
    "family": "משפחה",
}

FIRST_DAY = DAYS[0]
LAST_DAY = DAYS[-1]
FREE_DAY = {
    "id": 0,
    "region": "tokyo",
    "title": "יום חופשי בטוקיו",
    "tags": [],
    "car": False,
    "tour": False,
    "items": [],
    "meals": [],
}

for q in QUESTIONS:
    if q["type"] == "level":
        q["options"] = LEVELS


def read_answers(answers):
    """Check the answers and turn them into settings and tag weights.

    Returns (profile, error). Exactly one of them is None.
    """
    if not isinstance(answers, dict):
        return None, "answers must be a JSON object"

    profile = {"weights": {}}
    for q in QUESTIONS:
        value = answers.get(q["id"])
        if value is None or value == "":
            return None, f"missing answer: {q['id']}"

        if q["type"] == "number":
            try:
                number = int(value)
            except (TypeError, ValueError):
                return None, f"{q['id']} must be a number"
            if not q["min"] <= number <= q["max"]:
                return None, f"{q['id']} must be between {q['min']} and {q['max']}"
            profile[q["id"]] = number
            continue

        option = next((o for o in q["options"] if o["value"] == str(value)), None)
        if option is None:
            return None, f"bad answer for {q['id']}"

        if q["type"] == "level":
            add_weight(profile, q["tag"], int(option["value"]))
        if "set" in option:
            profile[q["id"]] = option["set"]
        for tag, weight in option.get("weights", {}).items():
            add_weight(profile, tag, weight)

    return profile, None


def add_weight(profile, tag, weight):
    profile["weights"][tag] = profile["weights"].get(tag, 0) + weight


def score(day, weights):
    return sum(weights.get(tag, 0) for tag in day["tags"])


def allowed(day, profile):
    if day["car"] and not profile["car"]:
        return False
    if day["tour"] and not profile["tours"]:
        return False
    return profile["kansai"] or day["region"] not in KANSAI


def area(region):
    return "kansai" if region in ("osaka", "kobe") else region


def build_day(number, day, previous, pace):
    items = day["items"]
    if pace == "relaxed":
        items = [i for i in items if not i["optional"]]

    transfer = ""
    if previous and area(previous["region"]) != area(day["region"]):
        transfer = (
            f"יום מעבר: נוסעים בשינקנסן מ{REGION_NAMES[previous['region']]} "
            f"ל{REGION_NAMES[day['region']]}"
        )

    return {
        "number": number,
        "region": day["region"],
        "region_name": REGION_NAMES[day["region"]],
        "title": day["title"],
        "transfer": transfer,
        "items": items,
        "meals": day["meals"],
    }


def make_plan(profile):
    weights = profile["weights"]
    middle = [d for d in DAYS[1:-1] if allowed(d, profile)]
    middle.sort(key=lambda d: (-score(d, weights), d["id"]))
    picked = middle[: profile["days"] - 2]
    picked.sort(key=lambda d: d["id"])

    free = [FREE_DAY] * (profile["days"] - 2 - len(picked))
    route = [FIRST_DAY] + picked + free + [LAST_DAY]
    days = []
    previous = None
    for number, day in enumerate(route, start=1):
        days.append(build_day(number, day, previous, profile["pace"]))
        previous = day

    top = sorted((t for t, w in weights.items() if w > 0), key=lambda t: -weights[t])
    cities = []
    for d in days:
        if d["region_name"] not in cities:
            cities.append(d["region_name"])

    return {
        "days": days,
        "cities": cities,
        "interests": [TAG_NAMES[t] for t in top[:4]],
    }
