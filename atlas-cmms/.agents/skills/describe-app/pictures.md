# Making an icon or a cover

Read only when the user asks for one to be made (describe-app, *The pictures*).

When the user asks you to make the icon or cover, make it **abstract** — the same family as the
covers the portal draws for apps without one — so a team's page reads as one set, not a collage.
Draw it with code (a script run once, outside `src/` — `uv run --with pillow python draw.py` works wherever
canvas does, Next.js app or not), not by hand:

- **One palette**, darkest to lightest, then one bright mark. Pick the one that suits the app (or,
  unsure, by its category), and not the one its neighbours on the team page use:

  | Palette | Background → shapes | Mark |
  |---|---|---|
  | deep teal | `#123538` `#1B4A4E` `#3E7C76` | `#D9A441` |
  | ochre | `#5A3E0E` `#8A6117` `#C08A2E` | `#F1D9A6` |
  | green | `#173E33` `#2A6350` `#4F8E74` | `#E7C873` |
  | brick | `#5C2219` `#8E3527` `#C0603F` | `#F0C08A` |
  | slate | `#1D2B3A` `#2F4157` `#56708F` | `#E3B65C` |
  | ink | `#141B1D` `#263235` `#4A5B5E` | `#C99A3C` |

- **Inspired by the title and description**: read them first, and let the shapes carry the app's
  idea as a feeling, not a picture of it — what it *does*, abstracted:

  | The app | An abstract idea for it |
  |---|---|
  | summarises articles | many thin bands that gather into one broad one |
  | translates | two waves of different colours meeting and overlapping |
  | plans shifts, rotas | a calm rhythm of rounded blocks in rows, one lit by the mark |
  | checks rights, verifies | a circle closing around the mark, steady and centred |
  | maps stories, connects things | a few circles joined by soft arcs |
  | live, breaking, alerts | a bright mark with rings spreading from it |

  The palette follows the same reading: warm (ochre, brick) for the lively, cool (teal, slate) for
  the calm and analytical. One sentence to the user says what you drew from — "two waves meeting,
  for translation".
- **Shapes: any, as long as it is abstract art that is easy on the eye.** These four are where the
  portal's own start — use one, or make your own in their spirit:
  - **horizon**: a sun (the mark) behind three rolling hills, darkest in front
  - **orbits**: concentric rings from one corner, the mark at their centre
  - **blocks**: four or five tilted, rounded panels, half see-through
  - **dunes**: broad diagonal bands sweeping across

  Arcs, overlapping circles, a single wave, soft stripes, a few floating pebbles — all fine, if:
  - **few and large**: three to six shapes, each big enough to read at the size of a card
  - **flat**: solid colours from the palette, overlaps by transparency — no outlines, no shadows,
    no textures beyond the grain, no fine detail
  - **calm**: one focal point (the mark, usually), room around it, gentle contrast — nothing that
    flickers, crowds the edges or fights the white title the card puts over it
- **The finish**: a diagonal gradient between the two darkest colours behind it; a soft white glow
  from the top-left (about 20%); a fine grain over everything (about 7%), so it is not flat. Then
  look at it on a dark page, where the portal shows it too: if the glow glares there, soften it.
- **The cover** (1600×600): the motif fills it, its focus inside the centre 1200×240. **The icon**
  (512×512): the same palette and motif, closer in, one shape filling the square.
- **Never**: words or letters, logos, people or faces, screenshots, photographs, emoji, clip-art of
  what the app does (no little documents and arrows) — inspired by it, never a drawing of it; the
  title says what it is, the picture makes it recognisable.

Save the cover as `src/static/cover.jpg` and the icon as `src/static/icon.png`, under their sizes in
KB; delete the script afterwards — it is not the app's.

`canvas validate` refuses a picture that is too big, not a PNG, JPEG or WebP, or not under
`src/static/`. Too big: ask for a smaller copy, or shrink that same picture if they agree.
