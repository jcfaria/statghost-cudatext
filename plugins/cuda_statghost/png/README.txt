STATghost plugin glyphs (VP-EB-1b native chrome)
================================================

Subset only — toolbar + sidebar. Not Explorer / Console / Plot.

  16px/ 24px/ 32px/   send, clear, armed, idle, power, kill, setting-lines;
                      sweave, knit, knit-html (Tinn colour, no tint);
                      ls, print, print_head, print_tail, names, str, plot,
                      help_selected, close_graphics, remove_objects, clear_all
                      (Tinn colour R-control, no tint);
                      next-line / play / export unused (reserve)
  statghost_24.png    sidebar / brand (also 32)

Tinn-R_D 16px extracts + generated 24/32 live in repo `w_todo/icons/`
(VP-WB-2 stash). Owner GO 2026-08-16: colour glyphs that also ship
here and are **not** tinted:

  Rnoweb   sweave / knit / knit-html
  R-control first cut  ls / print / head / tail / names / str / plot /
                       help_selected / close_graphics / remove_objects /
                       clear_all

Never upscale the **plugin** Flaticon set. Pick the largest folder <=
the host imagelist size.

Source drop (full SG copy + extras) lives at the companion repo
`png/` root — do not ship explorer_filter / explorer_popup here.

Recipe comments in chrome.py cite cuda_r_plugin + mission §5 OUT.
