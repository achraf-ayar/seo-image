# Photo credits

The four example photos in `originals/` were downloaded unchanged from Wikimedia Commons, where each
is marked **CC0 1.0 (public domain dedication)**. No attribution is required; credit is given anyway.
They were renamed to camera-style names (`IMG_xxxx.jpg`, `DSC_xxxx.jpg`) only to show a realistic
"before"; the photographers did not choose these names.

| File | Photo | Author | Licence | Commons page | Original source |
|------|-------|--------|---------|--------------|-----------------|
| `IMG_4821.jpg` | Blue coffee cup | rawpixel.com | CC0 1.0 | https://commons.wikimedia.org/wiki/File:Blue_coffee_cup_(Unsplash).jpg | https://unsplash.com/photos/CVYT72bMugw |
| `DSC_0412.jpg` | Living room | Jarosław Ceborski (jarson) | CC0 1.0 | https://commons.wikimedia.org/wiki/File:Living_room_(Unsplash).jpg | https://unsplash.com/photos/jn7uVeCdf6U |
| `IMG_7305.jpg` | Bread slices | Saral Shots | CC0 1.0 | https://commons.wikimedia.org/wiki/File:Bread_slices.jpg | Own work (uploaded to Commons) |
| `IMG_2290.jpg` | Cafe menu | Peter Miranda (petermiranda) | CC0 1.0 | https://commons.wikimedia.org/wiki/File:Cafe_menu_(Unsplash).jpg | https://unsplash.com/photos/ZpneNlSUyXQ |

Licence text: https://creativecommons.org/publicdomain/zero/1.0/

## Notes

- `IMG_2290.jpg` shows two out-of-focus passers-by in the background; they are not identifiable.
- `IMG_4821.jpg` has a dark, out-of-focus shape at the right edge; it is not identifiable.
- No brand logos or source-site watermarks are visible in any of the four photos.

## What the files in this folder are

- `originals/`: the downloaded photos, unmodified apart from the file names.
- `output/`: produced by running the seo-image skill on `originals/` with `--site example.com`
  (full quality; `report.json` is the skill's own report). Nothing here was edited by hand.
- The small copies used by the README live in `../images/`; they are made by
  `docs/build_readme_examples.py`.
