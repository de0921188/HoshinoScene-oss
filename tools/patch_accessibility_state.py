"""Keep a live connection signal for the accessibility checks during profile refresh.

The framework service list remains the primary check. The fallback is true only
between this app's onServiceConnected and onUnbind/onDestroy callbacks, so it
does not treat a saved permission as a running service or grant permissions.
Usage: python tools/patch_accessibility_state.py <apktool-decoded-directory>
"""
import argparse
from pathlib import Path

SERVICE = 'Lcom/omarea/vtools/AccessibilitySceneMode;'
FIELD = 'profileServiceConnected:Z'


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Unexpected Smali; refusing accessibility patch')
    return text.replace(old, new)


def service_patch(text):
    if FIELD in text:
        return text
    if '.method public onDestroy()V' in text or '.method public final onDestroy()V' in text:
        raise ValueError('Unexpected onDestroy override')
    text = once(text, '# static fields', '# static fields\n.field public static volatile '+FIELD+'\n')
    old = '    invoke-super {p0}, Landroid/accessibilityservice/AccessibilityService;->onServiceConnected()V\n'
    text = once(text, old, old+'\n    const/4 v0, 0x1\n\n    sput-boolean v0, '+SERVICE+'->'+FIELD+'\n')
    start = text.index('.method public final onUnbind(')
    end = text.index('.end method', start)
    old = '    const/4 v0, 0x0\n\n    iput-boolean v0, p0, '+SERVICE+'->B:Z'
    new = '    const/4 v0, 0x0\n\n    sput-boolean v0, '+SERVICE+'->'+FIELD+'\n\n    iput-boolean v0, p0, '+SERVICE+'->B:Z'
    method = once(text[start:end], old, new)
    text = text[:start]+method+text[end:]
    return text+'''
.method public onDestroy()V
    .locals 1
    const/4 v0, 0x0
    sput-boolean v0, '''+SERVICE+'->'+FIELD+'''
    invoke-super {p0}, Landroid/app/Service;->onDestroy()V
    return-void
.end method
'''


def page_patch(text):
    if FIELD in text:
        return text
    old = '    :goto_9\n    const-string v4, "dynamic_control"'
    new = '''    :goto_9
    if-nez v1, :profile_service_state_checked
    sget-boolean v1, '''+SERVICE+'->'+FIELD+'''
    :profile_service_state_checked
    const-string v4, "dynamic_control"'''
    return once(text, old, new)


def click_patch(text):
    if FIELD in text:
        return text
    old = '    :cond_1c\n    const/4 v5, 0x0\n'
    new = '''    :cond_1c
    sget-boolean v2, '''+SERVICE+'->'+FIELD+'''
    if-nez v2, :goto_e
    const/4 v5, 0x0
'''
    return once(text, old, new)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decoded', type=Path)
    args = parser.parse_args()
    changes = []
    for relative, transform in [('com/omarea/vtools/AccessibilitySceneMode.smali', service_patch),
                                ('a/bn0.smali', page_patch), ('a/hm0.smali', click_patch)]:
        matches = list(args.decoded.glob('smali*/'+relative))
        if len(matches) != 1:
            raise ValueError('Expected one '+relative)
        p = matches[0]
        changes.append((p, transform(p.read_text(encoding='utf-8'))))
    for p, text in changes:
        p.write_text(text, encoding='utf-8', newline='\n')
    print('Accessibility live-connection fallback patched')


if __name__ == '__main__':
    main()
