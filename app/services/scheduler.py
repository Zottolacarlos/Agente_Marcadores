from app.models.bookmark import BookmarkAnalysis


def build_7_day_schedule(items: list[BookmarkAnalysis]) -> dict[str, list[BookmarkAnalysis]]:
    selected = [x for x in items if x.recommended_action in {"ver_esta_semana", "ver_luego"}][:14]
    schedule = {f"Día {i}": [] for i in range(1, 8)}
    idx = 0
    for day in schedule:
        for _ in range(2):
            if idx < len(selected):
                schedule[day].append(selected[idx])
                idx += 1
    return schedule
