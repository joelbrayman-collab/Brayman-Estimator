"""Stage a screen-edition book for publishing as an artifact: title, viewport-fit meta, styles and body only."""
import sys, re
src, out = sys.argv[1], sys.argv[2]
s = open(src).read()
t = re.search(r"<title>.*?</title>", s).group(0)
style = s[s.index("<style>"):s.index("</style>") + 8]
body = s[s.index("<body>") + 6:s.rindex("</body>")]
open(out, "w").write(t + '<meta name="claude:viewport-fit-sides" content="cover">' + style + body)
print(out, len(t + style + body))
