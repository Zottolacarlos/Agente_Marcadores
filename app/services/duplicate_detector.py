def detect_duplicates(normalized_urls: list[str]) -> set[str]:
    seen = set()
    dups = set()
    for u in normalized_urls:
        if u in seen:
            dups.add(u)
        seen.add(u)
    return dups
