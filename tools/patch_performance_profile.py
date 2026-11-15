"""Patch the recovered APK's profile check without rebuilding incomplete Java.

Usage: python tools/patch_performance_profile.py <apktool-decoded-directory>
Only the author-name check in a.b11.d() changes. Source and profile-file
checks, external-module handling, resources and tuning parameters stay intact.
"""
import argparse
from pathlib import Path


def patch(text):
    start = text.index('.method public static d()Z')
    end = text.index('.end method', start)
    method = text[start:end]
    if '"SCENE N1"' in method:
        return text
    old = '''    const-string v2, "SCENE9"

    invoke-static {v0, v2}, La/wv;->e(Ljava/lang/Object;Ljava/lang/Object;)Z

    move-result v0
'''
    new = '''    const-string v2, "SCENE9"

    invoke-static {v0, v2}, La/wv;->e(Ljava/lang/Object;Ljava/lang/Object;)Z

    move-result v2

    if-nez v2, :profile_author_accepted

    const-string v2, "SCENE N1"

    invoke-static {v0, v2}, La/wv;->e(Ljava/lang/Object;Ljava/lang/Object;)Z

    move-result v0

    goto :profile_author_checked

    :profile_author_accepted
    const/4 v0, 0x1

    :profile_author_checked
'''
    if method.count(old) != 1:
        raise ValueError('Unexpected profile check; refusing to patch this APK')
    return text[:start] + method.replace(old, new) + text[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decoded', type=Path)
    args = parser.parse_args()
    files = list(args.decoded.glob('smali*/a/b11.smali'))
    if len(files) != 1:
        raise ValueError('Expected exactly one a/b11.smali')
    path = files[0]
    original = path.read_text(encoding='utf-8')
    result = patch(original)
    path.write_text(result, encoding='utf-8', newline='\n')
    print('Profile author compatibility patched' if result != original else 'Already patched')


if __name__ == '__main__':
    main()
