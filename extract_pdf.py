from pathlib import Path
import subprocess
import pandas as pd
import shutil

BASE = Path('Data')  # Put the five original PDFs here.

BIN = shutil.which('pdftotext') or '/Users/nurdauletigenov/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/bin/pdftotext'

rows = []
errors = []

for year in range(2022, 2027):
    text = subprocess.check_output([BIN, '-layout', str(BASE / f'grant_{year}.pdf'), '-']).decode()
    seen = []
    active = None
    section = 'general'

    for page, txt in enumerate(text.split('\f'), 1):
        for line in txt.splitlines():
            words = line.split()
            if not words:
                continue

            code = words[0].replace('В', 'B')

            if len(code) == 4 and code[0] == 'B' and code[1:].isdigit() and len(words) > 1 and words[1] == '-':
                active = None

            if code in ['B014', 'B015', 'B032', 'B034'] and code not in seen:
                active = code
                seen.append(code)
                section = 'general'

            if active is None:
                continue

            normalized = ' '.join(words)

            if normalized in ['ОБЩИЙ КОНКУРС', 'ЖАЛПЫ КОНКУРС']:
                section = 'general'
            if normalized in ['СЕЛЬСКАЯ КВОТА', 'АУЫЛ КВОТАСЫ']:
                section = 'rural'

            if len(words) > 2 and words[0].isdigit() and words[1].isdigit() and len(words[1]) == 9:
                found = False
                for j in range(2, len(words) - 1):
                    if words[j].isdigit() and words[j + 1].isdigit() and len(words[j + 1]) == 3 and 0 <= int(words[j]) <= 140:
                        quota = ' '.join(words[j + 2:])
                        if quota not in ['', 'ауылдық', 'ТЖ']:
                            errors.append([year, active, page, words[0], 'quota'])
                        
                        # ОПРЕДЕЛЯЕМ COMPETITION СРАЗУ (без потери данных)
                        # По умолчанию берём текущий section
                        competition = section
                        
                        # Если это 2024 год и указана конкретная квота — перезаписываем
                        if year == 2024:
                            if quota == 'ауылдық':
                                competition = 'rural'
                            elif quota == 'ТЖ':
                                competition = 'emergency'
                        
                        rows.append([
                            year,
                            active,
                            words[j],
                            words[j + 1],
                            competition
                        ])
                        found = True
                        break

                if not found:
                    errors.append([year, active, page, words[0], 'numeric columns'])

    print(year, 'done', flush=True)

pd.DataFrame(
    rows,
    columns=[
        'year',
        'group_code',
        'score',
        'university_code',
        'competition'
    ]
).to_csv('raw_no_names.csv', index=False)

assert not errors, errors
print('Extraction complete. Clean single-column competition saved.')