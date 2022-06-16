import math

# helper functions
def format_number(n):
    abbrevs = ['','k','M','B','T']
    n = float(n)
    ix = max(0,min(len(abbrevs)-1, int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))
    return '{:.2f}{}'.format(n / 10**(3 * ix), abbrevs[ix])
