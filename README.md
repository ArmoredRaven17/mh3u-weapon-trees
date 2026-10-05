# MH3U Weapon Trees

An interactive, in-browser map of every weapon upgrade tree in **Monster Hunter 3 Ultimate**: all
12 weapon classes (1,415 weapons) drawn as a tilted 2.5D map, a flat 2D diagram, or a free-orbit 3D
view. It's a port of the author's [MHGU Weapon Trees](https://github.com/ArmoredRaven17/mhgu-weapon-trees).

Pick a class and a tree from the bottom bar, then click any weapon to see its full stats: attack,
affinity, slots, element (bracketed when it needs Awaken), sharpness (base and Sharpness +1), Hunting
Horn notes, Gunlance shelling, Switch Axe phials, bow charges, arc shot and coatings, and bowgun
reload/recoil/deviation and ammo. It also shows the upgrade recipe, plus the forge recipe where the
smithy has one. You can tick weapons as **Made**, highlight made or unmade ones, and snip branches out
of the view. Snips and Made ticks are saved in your browser.

## How it differs from the MHGU app

MH3U has no weapon levels. Every upgrade is a separate weapon, so every node is one weapon, keyed by
the game's own weapon id. Each run of upgrades is drawn as one straight lane: the first upgrade the
game lists for a weapon carries its lane on, and any others branch off to the side. Lanes only
affect the layout. MHGU's "a branch stays open past the level it unlocks" rule doesn't exist in 3U,
so it's gone. Rarity is per weapon, from 1 to 10, in the game's own name colours.

## Where the data comes from

`docs/index.html` is a single self-contained page with no runtime fetches. Its data block is written by
[scripts/build.py](scripts/build.py) from sibling repos:

- **[mh3u-collection-tracker](https://github.com/ArmoredRaven17/mh3u-collection-tracker)** provides
  the weapon stats, recipes and upgrade links (`docs/data/`, which that repo reads from the game
  itself), the rarity icons, the monster theme icons, the textures and the font.
- **[mhgu-weapon-trees](https://github.com/ArmoredRaven17/mhgu-weapon-trees)** provides the coating
  icons and the Hunting Horn note glyph. The build recolours the glyph to the tracker's 3U note colours.

```
python scripts/build.py
```

The build needs Python 3.10+ and Pillow. Both repos default to siblings of this one; pass paths to
override. Only the region between the `DATA:BEGIN` / `DATA:END` markers is rewritten. Edit the app
code in place. Rebuild whenever the tracker's data changes.

## Local development

```
python -m http.server 8135 --directory docs
```

You can also open `docs/index.html` directly, since nothing is fetched.

## Licensing

Code is MIT (see [LICENSE](LICENSE)). Game data and icons are Capcom's. See [NOTICE.md](NOTICE.md).
Monster Hunter 3 Ultimate is © Capcom Co., Ltd. This is an unofficial fan project.

Most of this project's code was written with [Claude Code](https://claude.com/claude-code), working
from the author's direction.
