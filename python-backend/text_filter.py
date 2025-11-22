"""Text filtering utilities - exact port from TypeScript"""
import re


def remove_json_from_text(text: str) -> str:
    """
    MAKSYMALNIE AGRESYWNE FILTROWANIE - usuwa WSZYSTKIE JSONy i fragmenty techniczne
    Exact port from TypeScript removeJsonFromText function
    """
    if not text:
        return text
    
    cleaned = text
    
    # ETAP 1: ULTRA AGRESYWNE - usuń WSZYSTKIE fragmenty zawierające { (nawias klamrowy)
    cleaned = re.sub(r'\{[^\}]*$', ' ', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'\{[^\}]*\}', ' ', cleaned)
    
    # ETAP 2: Usuń fragmenty zaczynające się od { nawet bez zamknięcia
    cleaned = re.sub(r'\{.*$', ' ', cleaned, flags=re.MULTILINE)
    
    # ETAP 3: FILTROWANIE WSZYSTKICH WYWOŁAŃ FUNKCJI
    cleaned = re.sub(r'computer_use\s*\([^)]*\)', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'bash\s*\([^)]*\)', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'update_workflow\s*\([^)]*\)', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'screenshot\s*\([^)]*\)', ' ', cleaned, flags=re.IGNORECASE)
    
    # ETAP 4: Usuń częściowe wywołania funkcji (bez zamykającego nawiasu)
    cleaned = re.sub(r'computer_use\s*\(.*$', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'bash\s*\(.*$', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'update_workflow\s*\(.*$', ' ', cleaned, flags=re.IGNORECASE)
    
    # ETAP 5: Usuń standalone słowa kluczowe
    cleaned = re.sub(r'\bcomputer_use\b', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bupdate_workflow\b', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bcomputer\s*$', ' ', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    # ETAP 6: Usuń fragmenty z cudzysłowami i dwukropkami (typowe dla JSON)
    cleaned = re.sub(r'["\'][a-zA-Z_]+["\']\s*:\s*["\'][^"\']*["\']', ' ', cleaned)
    cleaned = re.sub(r'["\'][a-zA-Z_]+["\']\s*:', ' ', cleaned)
    
    # ETAP 7: Usuń współrzędne i tablice
    cleaned = re.sub(r'\[\s*\d+\s*,\s*\d+\s*\]', ' ', cleaned)
    cleaned = re.sub(r'\[\s*\d+[^\]]*$', ' ', cleaned)
    
    # ETAP 8: Usuń słowa kluczowe JSON
    cleaned = re.sub(r'["\']?name["\']?\s*:', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'["\']?parameters["\']?\s*:', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'["\']?action["\']?\s*:', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'["\']?coordinate["\']?\s*:', ' ', cleaned, flags=re.IGNORECASE)
    
    # ETAP 9: Usuń komendy specjalne i ich fragmenty
    cleaned = re.sub(r'!isfinish', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'!isf[a-z]*', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'!is[a-z]*', ' ', cleaned, flags=re.IGNORECASE)
    
    # ETAP 10: Usuń fragmenty rozpoczynające się od znaku specjalnego
    cleaned = re.sub(r'^[\{\[\"\'].*', ' ', cleaned, flags=re.MULTILINE)
    
    # ETAP 10.5: Usuń same nawiasy klamrowe i słowo assistant
    cleaned = re.sub(r'\{assistant', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\{user', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\{\s*$', ' ', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^\s*\{', ' ', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'\s+\{\s+', ' ', cleaned)
    
    # ETAP 11: CZYSZCZENIE KOŃCOWE
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
    cleaned = cleaned.strip()
    
    # ETAP 12: Jeśli po filtrowaniu został tylko whitespace, zwróć pustą string
    if not cleaned or re.match(r'^\s*$', cleaned):
        return ''
    
    return cleaned
