import re

with open('index.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

funcs = [
    'populateFicha',
    'populateConsolidado',
    'populateDistribucion',
    'populateEvoTable',
    'populateInstructivoCharts',
    'populateInstructivoRanking',
    'populateDistTableInstructivo',
    'populateTipologiaTable',
    'populateTendenciaTables',
    'renderMap',
    'updateMap',
    'buildConsolRankList'
]

for func in funcs:
    pattern = rf'function\s+{func}\s*\([^)]*\)\s*\{{'
    m = re.search(pattern, html)
    if m:
        start = m.start()
        # Find closing brace by counting braces
        brace_count = 0
        end = start
        for i in range(m.end()-1, len(html)):
            if html[i] == '{':
                brace_count += 1
            elif html[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = i + 1
                    break
        func_body = html[start:end]
        print(f"\n==========================================")
        print(f"FUNCION: {func} (Largo: {len(func_body)} caracteres)")
        print(f"==========================================")
        # Show first 40 lines
        lines = func_body.split('\n')
        for l in lines[:35]:
            print("  " + l[:100])
        if len(lines) > 35:
            print(f"  ... (+ {len(lines)-35} lineas más)")
    else:
        print(f"\nNo se encontró función {func}")
