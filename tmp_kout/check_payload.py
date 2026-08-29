import base64, gzip, re
src = open('notebooks/local_validation/local_validation.py', encoding='utf-8').read()
g = re.search(r"GOLDEN_GZ64 = \(\n(?:    \"[^\"]*\"\n)+\)", src).group(0)
c = re.search(r"CAND_GZ64 = \(\n(?:    \"[^\"]*\"\n)+\)", src).group(0)
gd = gzip.decompress(base64.b64decode(''.join(re.findall(r'"([^"]*)"', g))))
cd = gzip.decompress(base64.b64decode(''.join(re.findall(r'"([^"]*)"', c))))
print('golden bytes', len(gd), 'cand bytes', len(cd))
print('golden==attack.py:', gd == open('src/attack.py', 'rb').read())
print('cand==e23:', cd == open('src/attack_e23_stackturn.py', 'rb').read())
