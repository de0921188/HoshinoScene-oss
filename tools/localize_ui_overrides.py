"""Localize hardcoded benchmark/monitor UI, preserving APK resource IDs.

Only selected binary XML string pools and activity const-string
display labels are changed. Binary XML string indices and node chunks stay
unchanged; the resource table and tuning/benchmark commands are untouched.
Requires opencc. Usage: python tools/localize_ui_overrides.py <decoded-dir>
"""
import argparse
import json
import re
import struct
from pathlib import Path
import opencc

HAN = re.compile('[\u4e00-\u9fff]')


def read_length(data, pos, utf8):
    step, mask, shift = (1, 0x80, 8) if utf8 else (2, 0x8000, 16)
    n = data[pos] if utf8 else struct.unpack_from('<H', data, pos)[0]
    pos += step
    if n & mask:
        extra = data[pos] if utf8 else struct.unpack_from('<H', data, pos)[0]
        pos += step
        n = ((n & (mask-1)) << shift) | extra
    return n, pos


def length(n, utf8):
    if utf8:
        if n > 0x7fff:
            raise ValueError('XML string too long')
        return bytes([n]) if n < 128 else bytes([(n >> 8) | 128, n & 255])
    return struct.pack('<H', n) if n < 0x8000 else struct.pack('<HH', (n >> 16) | 0x8000, n & 0xffff)


def patch_xml(data, convert):
    if struct.unpack_from('<H', data)[0] != 3:
        raise ValueError('Expected binary XML')
    chunks, changes, pos = [], 0, struct.unpack_from('<H', data, 2)[0]
    while pos < len(data):
        typ, header, size = struct.unpack_from('<HHI', data, pos)
        if size < header or pos+size > len(data):
            raise ValueError('Invalid XML chunk')
        chunk = data[pos:pos+size]
        if typ == 1:
            count, styles, flags, start, style_start = struct.unpack_from('<IIIII', chunk, 8)
            if styles or style_start:
                raise ValueError('Styled XML pools are not supported')
            utf8 = bool(flags & 256)
            strings, offsets = bytearray(), []
            for i in range(count):
                at = start + struct.unpack_from('<I', chunk, header+i*4)[0]
                n, at = read_length(chunk, at, utf8)
                if utf8:
                    n, at = read_length(chunk, at, True)
                    original = chunk[at:at+n].decode('utf-8')
                else:
                    original = chunk[at:at+n*2].decode('utf-16-le')
                value = convert(original) if HAN.search(original) else original
                changes += value != original
                offsets.append(len(strings))
                units = len(value.encode('utf-16-le')) // 2
                if utf8:
                    encoded = value.encode('utf-8')
                    strings += length(units, True)+length(len(encoded), True)+encoded+b'\0'
                else:
                    strings += length(units, False)+value.encode('utf-16-le')+b'\0\0'
            strings += b'\0' * (-len(strings) % 4)
            new_start = header+4*count
            out = bytearray(chunk[:header])
            struct.pack_into('<I', out, 4, new_start+len(strings))
            struct.pack_into('<III', out, 16, flags & ~1, new_start, 0)
            out += struct.pack('<'+'I'*count, *offsets)+strings
            chunk = bytes(out)
        chunks.append(chunk)
        pos += size
    out = bytearray(data[:struct.unpack_from('<H', data, 2)[0]]+b''.join(chunks))
    struct.pack_into('<I', out, 4, len(out))
    return bytes(out), changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decoded', type=Path)
    args = parser.parse_args()
    # Character conversion avoids repeated phrase substitutions on existing
    # Traditional text (some converters turn 演算法 into 演演算法).
    convert = opencc.OpenCC('s2tw').convert
    def display(value):
        return convert(value).replace('自定義監視器', '自訂監視器').replace('文本', '文字')
    names = {'fragment_nav.xml', 'activity_perf_bench.xml', 'activity_power_bench.xml',
             'dialog_power_bench_faq.xml', 'dialog_monitor.xml', 'activity_monitor_designer.xml',
             'fw_monitor.xml', 'fw_monitor2.xml', 'fw_monitor_mini.xml'}
    for path in (args.decoded/'res').glob('layout*/*.xml'):
        if path.name in names:
            original = path.read_bytes()
            result, count = patch_xml(original, convert)
            if count:
                # A second pass must preserve every translated string.
                assert patch_xml(result, convert)[1] == 0
                path.write_bytes(result)
                print(path.name, count, 'display strings localized')
    paths = []
    for name in ['ActivityPerfBench', 'ActivityMonitorDesigner']:
        paths.extend(args.decoded.glob('smali*/com/omarea/vtools/activities/'+name+'.smali'))
    for path in paths:
        text = path.read_text(encoding='utf-8')
        def replace(match):
            value = json.loads(match.group(2))
            if HAN.search(value):
                return match.group(1)+json.dumps(display(value), ensure_ascii=True)
            return match.group(0)
        text = re.sub(r'(^\s*const-string(?:/jumbo)?\s+\w+,\s*)("(?:[^"\\]|\\.)*")', replace, text, flags=re.M)
        path.write_text(text, encoding='utf-8', newline='\n')
    # These two monitor formatter prefixes live in an obfuscated shared class.
    # Replace only the exact display labels; leave all other constants intact.
    for path in args.decoded.glob('smali*/a/*.smali'):
        text = path.read_text(encoding='utf-8')
        def prefixes(match):
            try:
                value = json.loads(match.group(2))
            except ValueError:
                return match.group(0)
            if value.startswith(('刷新间隔', '缩放')):
                return match.group(1)+json.dumps(convert(value), ensure_ascii=True)
            return match.group(0)
        result = re.sub(r'(^\s*const-string(?:/jumbo)?\s+\w+,\s*)("(?:[^"\\]|\\.)*")', prefixes, text, flags=re.M)
        if result != text:
            path.write_text(result, encoding='utf-8', newline='\n')
    print('Benchmark and monitor UI localization complete')


if __name__ == '__main__':
    main()
