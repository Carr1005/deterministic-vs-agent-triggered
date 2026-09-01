# Views for tools/viewer. Each module exposes the small contract serve.py expects:
#
#   ID, LABEL      the URL segment and the tab label
#   TITLE          the <title>; a constant, since neither page needs a dynamic one yet
#   FOOTER         this page's footer sentence — the two pages make materially different
#                  claims about what they read, so the wording stays with the view
#   CSS, JS        emitted after the shell's, and only on this view's page
#   render()       the ENTIRE body below the tab bar, including the view's own <header>
#   signature()    a cheap change fingerprint for /state/<id>, or None for no polling
#
# A view whose signature() moves is rebuilt in the reader's open tab. Give any <details>
# the reader might have opened a stable `id`: the shell stashes the open ones across that
# reload and reopens them, and cards without ids come back closed.
#
# A view owns its whole body on purpose: the two pages are meant to grow in different
# directions, and the shell should never be the thing that has to change when one does.
