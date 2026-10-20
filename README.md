# Autopost na fanpage (GitHub Actions + Facebook Graph API)

Co godzinę GitHub Actions sprawdza katalog `posts/` i publikuje na stronie Facebook posty,
które mają `status: ready` i `publish_at` w przeszłości. Po publikacji status zmienia się na `published`.

## Format posta (`posts/RRRR-MM-DD-nazwa.md`)

```markdown
---
publish_at: 2026-10-20T09:00:00+02:00   # ze strefą czasową (lato +02:00, zima +01:00)
status: draft                            # draft -> ready -> published
link: https://phinance.pl                # opcjonalnie
image: images/grafika.jpg                # opcjonalnie, ścieżka w repo
---
Treść posta.
```

- `draft` – szkic, nic się nie dzieje.
- `ready` – zatwierdzony, wyjdzie w terminie `publish_at` (z opóźnieniem do kilkunastu minut).
- `published` – ustawia automat po publikacji.

## Konfiguracja (jednorazowo)

Settings → Secrets and variables → Actions:

- `FB_PAGE_ID` – ID strony
- `FB_PAGE_TOKEN` – bezterminowy token strony (uprawnienia: `pages_manage_posts`, `pages_read_engagement`, `pages_show_list`)

## Test bez publikowania

Actions → „Publikuj posty” → Run workflow → zaznacz `dry_run`.

## Eksport istniejących postów (archiwum do analizy stylu)

```bash
read -s "FB_PAGE_TOKEN?Token strony: "; export FB_PAGE_TOKEN; echo
python3 scripts/export_posts.py --limit 200 --insights
```

Zapisuje posty do `archive/` (po jednym pliku `.md` + `index.csv` z reakcjami, komentarzami, zasięgiem).
Wymaga uprawnień `pages_read_engagement` i `pages_read_user_content`.

## Grafiki do postów

Są dwa sposoby, żeby post wyszedł ze zdjęciem:

1. Wrzuć plik do `images/` o **takiej samej nazwie jak post**, np. `images/2026-12-01-obligacje-skarbowe-od-100-zl.jpg` (też `.jpeg` lub `.png`). Skrypt sam go znajdzie.
2. Albo wpisz ścieżkę w nagłówku posta: `image: images/grafika.jpg`.

Gdy jest grafika, tekst posta trafia jako podpis zdjęcia. Posty bez grafiki wychodzą jako zwykły tekst.

Pole `zrodlo:` w postach wskazuje oryginał w `archive/`. Skrypt je ignoruje.

### Generator grafik

Markowe grafiki (tytuł, hashtag w prawym górnym rogu, zdjęcie, dane kontaktowe) powstają skryptem `scripts/make_graphics.py` (wymaga Pillow). Tytuły, podtytuły, hashtagi i numery zdjęć są w `assets/grafiki.csv`, a wycięte zdjęcia w `assets/photos/`. Po zmianie tekstu w CSV uruchom skrypt ponownie, a grafika zostanie odtworzona.
