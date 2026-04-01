import re

OPEN_SANS = "'Open Sans', sans-serif"

test1 = "font-family: 'Open Sans', sans-serif;Open Sans&quot;, Helvetica, Arial, sans-serif; font-weight: bold; line-height: 28px;"
test2 = 'font-family: &quot;Open Sans&quot;, Helvetica, Arial, sans-serif; font-weight: bold;'
test3 = "font-family: 'Open Sans', sans-serif; font-weight: bold;"
test4 = "color: rgb(85, 85, 85); font-family: 'Open Sans', sans-serif;Open Sans&quot;, Arial, sans-serif; font-size: 15px;"


def fix_style_attr(style_value: str) -> str:
    """Fix font-family in a CSS style string by splitting on CSS property boundaries."""
    # Split on '; ' followed by a CSS property name (word chars + colon)
    props = re.split(r';\s*(?=[\w-]+\s*:)', style_value)
    result = []
    for prop in props:
        prop = prop.strip().rstrip(';')
        if re.match(r'font-family\s*:', prop):
            result.append(f'font-family: {OPEN_SANS}')
        else:
            result.append(prop)
    return '; '.join(result)


def fix_font_family(html: str) -> str:
    """Fix font-family in all style attributes."""
    def fix_style(m):
        quote = m.group(1)
        style_val = m.group(2)
        fixed = fix_style_attr(style_val)
        return f'style={quote}{fixed}{quote}'
    return re.sub(r'style=(["\'])([^"\']*?)\1', fix_style, html)


print("Testing fix_style_attr directly:")
for t in [test1, test2, test3, test4]:
    print("IN: ", repr(t[:80]))
    print("OUT:", repr(fix_style_attr(t)[:80]))
    print()
