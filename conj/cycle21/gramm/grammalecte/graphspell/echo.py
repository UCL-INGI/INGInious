#!python3

# The most boring yet indispensable function: print!


import sys


_CHARMAP = str.maketrans({  'œ': 'ö',  'Œ': 'Ö',  'ʳ': "r",  'ᵉ': "e",  '…': "_",  \
                            '“': '"',  '”': '"',  '„': '"',  '‘': "'",  '’': "'",  \
                            'ā': 'â',  'Ā': 'Â',  'ē': 'ê',  'Ē': 'Ê',  'ī': 'î',  'Ī': 'Î',  \
                            'ō': 'ô',  'Ō': 'Ô',  'ū': 'û',  'Ū': 'Û',  'Ÿ': 'Y',  \
                            'ś': 's',  'ŝ': 's',  \
                            '—': '-',  '–': '-'
                         })


def echo (obj, sep=' ', end='\n', file=sys.stdout, flush=False):
    """ Print for Windows to avoid Python crashes.
        Encoding depends on Windows locale. No useful standard.
        Always returns True (useful for debugging)."""
    if sys.platform != "win32":
        print(obj, sep=sep, end=end, file=file, flush=flush)
        return True
    try:
        print(str(obj).translate(_CHARMAP), sep=sep, end=end, file=file, flush=flush)
    except:
        print(str(obj).encode('ascii', 'replace').decode('ascii', 'replace'), sep=sep, end=end, file=file, flush=flush)
    return True
