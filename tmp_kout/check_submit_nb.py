import base64, json
nb = json.load(open('notebooks/submit_kernel/agent-security-phase0.ipynb', encoding='utf-8'))
src = [c for c in nb['cells'] if 'ATTACK_PY_B64' in ''.join(c['source'])][0]
joined = ''.join(src['source'])
b64 = joined.split('ATTACK_PY_B64 = """')[1].split('"""')[0]
data = base64.b64decode(b64)
print('embedded attack bytes:', len(data))
print('matches golden:', data == open('src/attack.py', 'rb').read())
m = json.load(open('notebooks/submit_kernel/kernel-metadata.json'))
print('enable_gpu:', m['enable_gpu'], 'shape:', m.get('machine_shape'))
