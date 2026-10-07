# Notices and Attributions

The original source code of this project is MIT-licensed (see [LICENSE](LICENSE)). The materials
below are not covered by that licence.

## Game IP

**Monster Hunter 3 Ultimate** and all related names, equipment, monsters, icons and data are
trademarks and © Capcom Co., Ltd. This project is an **unofficial fan-made weapon-tree viewer**. It is
not affiliated with, endorsed by, or sponsored by Capcom.

## Game data and icons

All weapon stats, names, recipes and upgrade links in `docs/index.html` are embedded at build time
by [scripts/build.py](scripts/build.py) from the
[MH3U Collection Tracker](https://github.com/ArmoredRaven17/mh3u-collection-tracker)'s generated
`docs/data/`. That project reads them from a personally owned copy of the game, and its NOTICE
covers how. The icons come from the same project and are all the game's own: the weapon icons in its
Rare 1-10 colours, the coating bottles in each coating's own colour, and the theme monster icons.
**No game files are redistributed.**

How weapons are grouped into lanes is this project's own layout choice and has no effect in the
game. See `scripts/build.py`.

## Icons from other projects

- **The Hunting Horn note glyph** comes from mhgu-editor and is recoloured here. It appears to be
  original artwork for that project.
- **The camera-toggle book icons** come from mhgu-editor, as in the MHGU Weapon Trees page.

## UI assets

The titlebar, theme picker, textures and the MHFU font are shared with the same author's MHGU fan
apps. The MHGU Weapon Trees NOTICE gives their sources.

## Development: AI assistance

A large share of this project's code was written with **[Claude Code](https://claude.com/claude-code)**
(Anthropic), directed and reviewed by the author.
