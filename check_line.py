with open('app/exercises/data.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open('line_1441.txt', 'w', encoding='utf-8') as f:
    f.write(repr(lines[1440]))
