"""Check exact system permission before asking to activate accessibility again.

Run after patch_accessibility_state.py. This adds a read-only permission check;
it does not grant permissions or rewrite secure settings.
"""
import argparse
from pathlib import Path

CALL = 'Lcom/omarea/vtools/AccessibilityAuthorization;->isAuthorized(Landroid/content/Context;)Z'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decoded', type=Path)
    args = parser.parse_args()
    changes = []
    for name in ['bn0', 'hm0', 'gy']:
        paths = list(args.decoded.glob('smali*/a/'+name+'.smali'))
        if len(paths) != 1: raise ValueError('Unexpected '+name)
        path = paths[0]; text = path.read_text(encoding='utf-8')
        if CALL in text: continue
        if name == 'bn0':
            old = '    :profile_service_state_checked\n    const-string v4, "dynamic_control"'
            new = '''    :profile_service_state_checked
    if-nez v1, :profile_permission_checked
    invoke-virtual {p0}, La/gk0;->L()Landroid/content/Context;
    move-result-object v4
    invoke-static {v4}, '''+CALL+'''
    move-result v1
    :profile_permission_checked
    const-string v4, "dynamic_control"'''
        elif name == 'hm0':
            old = '    if-nez v2, :goto_e\n    const/4 v5, 0x0'
            new = '''    if-nez v2, :goto_e
    invoke-virtual {v14}, La/gk0;->L()Landroid/content/Context;
    move-result-object v2
    invoke-static {v2}, '''+CALL+'''
    move-result v2
    if-nez v2, :goto_e
    const/4 v5, 0x0'''
        else:
            start = text.index('.method public static O(Landroid/content/Context;)Z')
            end = text.index('.end method', start)
            method = text[start:end]
            if method.count('    .locals 3\n') != 1: raise ValueError('Unexpected helper registers')
            method = method.replace('    .locals 3\n', '    .locals 4\n\n    move-object v3, p0\n')
            old = '    :cond_1\n    return v1'
            new = '''    :cond_1
    if-nez v1, :permission_result
    sget-boolean v1, Lcom/omarea/vtools/AccessibilitySceneMode;->profileServiceConnected:Z
    if-nez v1, :permission_result
    invoke-static {v3}, '''+CALL+'''
    move-result v1
    :permission_result
    return v1'''
            if method.count(old) != 1: raise ValueError('Unexpected accessibility helper')
            text = text[:start]+method.replace(old,new)+text[end:]
            changes.append((path,text));continue
        if text.count(old) != 1: raise ValueError('Unexpected '+name+' check')
        changes.append((path,text.replace(old,new)))
    for path,text in changes:path.write_text(text,encoding='utf-8',newline='\n')
    service = list(args.decoded.glob('smali*/com/omarea/vtools/AccessibilitySceneMode.smali'))
    if len(service)!=1:raise ValueError('Unexpected service location')
    dest=service[0].with_name('AccessibilityAuthorization.smali')
    dest.write_bytes(Path(__file__).with_name('smali').joinpath(dest.name).read_bytes())
    print('Read-only accessibility permission fallback patched')


if __name__=='__main__':main()
