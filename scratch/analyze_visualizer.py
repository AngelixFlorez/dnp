import re
import json

with open('index.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

print("Script src tags:", re.findall(r'<script[^>]*src=[\'"]([^\'"]+)[\'"]', html))
print("JSON references:", set(re.findall(r'[\'"][^\'"]*\.json[\'"]', html)))
print("Data assignments:", re.findall(r'(?:const|var|let)\s+([a-zA-Z0-9_]*data[a-zA-Z0-9_]*)\s*=', html, re.I))

# Find the main data loading block
matches = [m.start() for m in re.finditer(r'datos_idf\.json', html)]
for idx in matches:
    print("\nContext around datos_idf.json:")
    print(html[max(0, idx-200):min(len(html), idx+300)])

# Find the main headings and layout cards in index.html
headings = re.findall(r'<h[1-4][^>]*>(.*?)</h[1-4]>', html, re.DOTALL)
print("\n=== HEADINGS IN INDEX.HTML ===")
for h in headings[:30]:
    clean_h = re.sub(r'<[^>]+>', '', h).strip()
    if clean_h:
        print("  -", clean_h)

# Let's inspect filters, select elements
selects = re.findall(r'<select[^>]*id=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</select>', html, re.DOTALL)
print("\n=== SELECT FILTERS IN INDEX.HTML ===")
for sid, opts in selects:
    opt_labels = re.findall(r'<option[^>]*>([^<]+)</option>', opts)
    print(f"  Select #{sid}: {opt_labels[:10]}")

