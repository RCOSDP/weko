# Design Customization with Widget Design

This document describes how to customize the look of a WEKO3 repository **from
the administration screens**, without touching the source code. This is the
approach implemented by the `weko-gridlayout` module ("Widget" and "Page
Layout" under the **Web Design** admin category), combined with a few
theme-level settings in `weko-admin` and `weko-theme`.

For the other customization route — replacing the whole public UI with your own
front-end application (the AMS pattern) — see
[DESIGN_CUSTOMIZATION_FRONTEND.md](./DESIGN_CUSTOMIZATION_FRONTEND.md).

---

## 1. When to use this approach

Use Widget Design when you want to:

- change the top page, header, footer and navigation of the repository;
- add free-form HTML/rich-text blocks, notices, "new arrivals" lists and access
  counters;
- publish extra static pages (about, policy, contact, …) under your own URLs;
- give each community/index its own top page;
- do all of the above per language.

Everything is stored in the database and is editable by an administrator at
runtime. No rebuild, no redeploy, no code change.

You will hit the limits of this approach when you need a different information
architecture (custom search UI, custom item detail layout, a design system of
your own). At that point, move to the full front-end customization route.

---

## 2. Concepts and data model

Source: `modules/weko-gridlayout/weko_gridlayout/models.py`

| Table | Model | Meaning |
| --- | --- | --- |
| `widget_type` | `WidgetType` | The catalogue of widget kinds that can be created (`Free description`, `Notice`, …). Seeded by CLI, see §3. |
| `widget_items` | `WidgetItem` | One configured widget: its type, owning repository (community), JSON `settings`, enabled/deleted flags and an edit lock. |
| `widget_multi_lang_data` | `WidgetMultiLangData` | Per-language label and description for a widget. |
| `widget_design_setting` | `WidgetDesignSetting` | The layout (grid positions) of widgets for one repository — i.e. the main/top page. |
| `widget_design_page` | `WidgetDesignPage` | An additional page: `title`, `url`, `content`, `settings` (its own widget layout), `is_main_layout`. |
| `widget_design_page_multi_lang_data` | `WidgetDesignPageMultiLangData` | Per-language page title. |

Two identifiers matter:

- **`repository_id`** — the community the design belongs to. The whole-site
  design uses `Root Index` (`WEKO_THEME_DEFAULT_COMMUNITY`); a community design
  uses that community's identifier.
- **`url`** — the public path of a `WidgetDesignPage`. For a community page the
  UI prefixes `/c/<community_id>/page` automatically.

### Built-in widget types

Seeded by `scripts/populate-instance.sh` (see the
`sphinxdoc-create-widget_type-data` block):

| Type | Purpose |
| --- | --- |
| `Free description` | Rich-text/HTML block (WYSIWYG editor with KaTeX support). |
| `Notice` | Rich text with a "read more" fold; you set the hidden part and the "read more" label. |
| `New arrivals` | Recently registered items; you set how many results and the "new" period in days, and can expose an RSS feed. |
| `Access counter` | Site access counter with a start value, a start date and preceding/following messages. |
| `Main contents` | Placeholder for WEKO's own search/index content. A page that contains this widget is rendered with the theme front page template. |
| `Menu` | Navigation menu over your Widget Design pages; orientation plus background/active/text colours. |
| `Header` | Site header; also holds the fixed-header background and text colours. |
| `Footer` | Site footer. |

---

## 3. Prerequisites (fresh instance)

Both steps are already part of `scripts/populate-instance.sh`; run them manually
only if you are bootstrapping an instance by hand.

```bash
# 1. Register the widget types (id, display name)
invenio widget_type create "Free description" "Free description"
invenio widget_type create "Access counter"   "Access counter"
invenio widget_type create "Notice"           "Notice"
invenio widget_type create "New arrivals"     "New arrivals"
invenio widget_type create "Main contents"    "Main contents"
invenio widget_type create "Menu"             "Menu"
invenio widget_type create "Header"           "Header"
invenio widget_type create "Footer"           "Footer"

# 2. Create the bucket that stores widget images and other static files
invenio widget init
```

Register the languages you intend to use first (**Setting › Language** in the
admin), because widget labels and descriptions are entered per registered
language.

---

## 4. Step-by-step customization

### 4.1 Create the widgets — Web Design › Widget

`/admin/widgetitem/`

1. **New** → choose **Repository** (`Root Index` for the whole site, or a
   community) and **Widget Type**.
2. Fill the common settings:
   - **Label** and **Description** per language (the description field is the
     rich-text body for `Free description`, `Notice`, `Header` and `Footer`).
   - **Label colour / text colour / background colour**, **frame border colour**
     and **border style**.
   - **Theme**: `Default`, `Simple` or `Side Line`. `Simple` drops the frame and
     border settings.
   - **Enable** — unchecked widgets stay in the list but are not rendered.
3. Fill the type-specific settings (new arrivals count and period, access
   counter start value and messages, notice fold and "read more" label, menu
   colours and the pages to show, fixed-header colours).
4. Save. Widgets are edit-locked while another administrator has them open; the
   lock can be released from the same screen.

Images and other files used inside a rich-text widget are uploaded through the
widget editor and stored in the widget bucket
(`POST /widget/uploads/<community_id>`, served back from
`/widget/uploaded/<filename>/<community_id>`). The size limit is
`WEKO_GRIDLAYOUT_FILE_MAX_SIZE` (16 MB by default).

### 4.2 Lay out the top page — Web Design › Page Layout

`/admin/widgetdesign/`

1. Select the **Repository**. The page selector then shows `Main Layout` plus
   every Widget Design page of that repository.
2. With `Main Layout` selected, drag widgets from the list into the grid.
   Resize and move them; the **Preview** pane reflects the saved geometry
   (`x`, `y`, `width`, `height` per widget).
3. **Save**.

Notes:

- Put a `Header` widget at the top and a `Footer` widget at the bottom if you
  want them to replace the stock theme header/footer. When a design supplies
  them, the theme hides its own header/footer blocks
  (`render_widgets` / `render_header_footer` in
  `modules/weko-theme/weko_theme/templates/weko_theme/base.html`).
- A layout that contains the `Main contents` widget is rendered with
  `THEME_FRONTPAGE_TEMPLATE`, so WEKO's search box, index tree and search
  results appear inside your layout.

### 4.3 Add extra pages

On the same screen, use the page editor:

1. **Title** (per language), **URL** and optional **content**.
2. Tick **Main Layout** if this page should be the repository's top page.
3. Save, then lay widgets out on that page exactly as for the main layout.

Rules enforced by the model and the UI:

- The URL must be unique across all Widget Design pages.
- For a community, `/c/<community_id>/page` is prepended automatically.
- Pages are registered as Flask URL rules at start-up
  (`preload_pages()` in `views.py`); a page created afterwards is picked up by
  the 404 handler and registered on first access, so no restart is needed.
- A page without `Main contents` is rendered with
  `WEKO_GRIDLAYOUT_DEFAULT_PAGES_TEMPLATE`
  (`weko_gridlayout/pages/default_page.html`).
- Creating a page does **not** publish a link to it. Every page becomes a
  candidate entry for the `Menu` widget, but you must put it in that widget's
  *Show* list before visitors can navigate to it — see §4.4.

### 4.4 Wire up navigation — the Menu widget

The `Menu` widget is what turns your Widget Design pages into a navigation bar.
There is no separate "menu structure" screen: **every page you create in Page
Layout is automatically a candidate menu entry**, and the Menu widget decides
which of them are shown, in which order, and with which colours.

#### 4.4.1 Creating the menu

In **Web Design › Widget**, create a widget of type `Menu` for the same
repository as the pages. Its settings are:

| Setting | Key | Meaning |
| --- | --- | --- |
| Display Orientation | `menu_orientation` | `horizontal` (Bootstrap navbar) or `vertical` (stacked pills). Default `horizontal`. |
| Background Color | `menu_bg_color` | Menu bar background. |
| Default Color | `menu_default_color` | Link text colour. |
| Active Background Color | `menu_active_bg_color` | Background of the current/hovered entry. |
| Active Color | `menu_active_color` | Text colour of the current/hovered entry. |
| **Show/Hide Pages** | `menu_show_pages` | The entries themselves — see below. |

Then place the Menu widget on the layout in **Page Layout**, exactly like any
other widget. It is usually put directly under the Header widget and given the
full grid width. A page can carry more than one Menu widget; each is rendered
with its own generated CSS class, so their colours do not collide.

#### 4.4.2 Show / Hide: choosing the entries

**Show/Hide Pages** is a two-list picker:

```
      ┌──────────────── Show ────────────────┐        ┌──────── Hide ────────┐
  ↑   │ Main Layout                          │        │ Internal draft page  │
  ↓   │ About this repository                │   →    │ Old notice page      │
      │ Usage policy                         │   ←    │                      │
      │ Contact                              │        │                      │
      └──────────────────────────────────────┘        └──────────────────────┘
```

- The **Show** list (left) is what appears in the menu, **in list order**.
- The **Hide** list (right) is everything excluded from this menu. The pages
  still exist and stay reachable by URL — hiding only removes the link.
- `→` moves the selected entries Show → Hide, `←` moves them back.
- `↑` / `↓` reorder the Show list; that order is stored verbatim in
  `menu_show_pages` and is the order rendered on the site.

Behaviour worth knowing:

- **New pages are not added to an existing menu automatically.** When you create
  a Menu widget, every page of the repository (plus `Main Layout`) starts in
  *Show*; but when you later add a page, you must reopen the Menu widget and move
  it into *Show* yourself. A page that is neither in Show nor in Hide of any menu
  is simply not linked anywhere.
- **`Main Layout` is a pseudo-entry** representing the repository top page. It is
  rendered as the navbar brand on the left of the bar (not as an ordinary list
  item) and links to `/` — or to `/?c=<community_id>` for a community. Its label
  is the title of the page flagged *Main Layout*; if no page carries that flag,
  the literal text `Main Layout` is used. Move it to *Hide* if you do not want a
  home link in the bar.
- **Page titles are the menu labels**, resolved per language from the page's
  multilingual title, falling back to the base title when that language has no
  translation. Renaming a page renames its menu entry.
- **Deleted pages disappear silently.** A page id left in `menu_show_pages` that
  no longer resolves is skipped when the menu is built, so a deleted page will
  not break the bar — but the stale id stays in the setting until you next save
  the widget.
- The entry matching the current URL gets the `active` class and is painted with
  the active colours, so visitors can see where they are.
- Community pages are linked with the community context preserved (`?c=<id>`
  appended, or the `/c/<id>/page` prefix normalised away) so that navigation
  stays inside the community.

#### 4.4.3 Hiding the whole menu

Three levels of "hiding", from coarsest to finest:

1. **Uncheck `Enable` on the Menu widget** (Web Design › Widget) — the widget is
   kept but not rendered on any page.
2. **Remove the Menu widget from a layout** (Page Layout) — the menu disappears
   from that page only; other pages that still contain it keep their bar. This is
   how you give, for example, the top page a menu and leave a landing page
   without one.
3. **Move individual pages to *Hide*** — the bar stays, minus those entries.

Note that the widget's own `Label` (the frame caption drawn above a widget) is
usually turned off for `Menu`, `Header` and `Footer` widgets; use the `Simple`
theme for those so no frame or label is drawn around the bar.

#### 4.4.4 How the menu is built at run time

The menu is assembled in the browser, not in the template:

1. `weko_theme/static/js/weko_theme/widget.js` sees a widget of type `Menu` in
   the design and calls
   `GET /api/admin/get_page_endpoints/<widget_id>/<current_language>`.
2. `WidgetDataLoaderServices.get_widget_page_endpoints()`
   (`weko_gridlayout/services.py`) walks `menu_show_pages` **in order**, loads
   each `WidgetDesignPage`, and returns `{url, title, is_main_layout}` per entry,
   with the title already resolved for the requested language.
3. The script emits a Bootstrap navbar (or stacked pills for `vertical`) plus a
   `<style>` block scoped to `widgetNav_<widget_id>`, marks the current entry
   `active`, and injects it into the widget's grid cell.

Consequences: the menu is language-aware without a page reload path of its own,
it is subject to the same design cache TTL as the rest of the layout (§7), and
the entry list is only as fresh as the widget's saved `menu_show_pages`.

### 4.5 Multilingual design

Every widget carries a label and description per registered language, and every
page carries a title per language. The public site loads the design for the
current UI language (`/api/admin/load_widget_design_setting/<lang>` and
`/api/admin/load_widget_design_page_setting/<page_id>/<lang>`) and falls back to
the default language when a translation is missing. Design the layout once —
only the text is per language.

### 4.6 Community (index) specific design

Select the community in the **Repository** selector and build a separate layout
and page set for it. Community pages are served under
`/c/<community_id>/...`; the theme renders the community header and the
community footer widget instead of the site-wide ones.

---

## 5. Settings outside Widget Design

These live in other admin screens but are part of the same "no-code" design
surface.

| Screen | What it controls | Backing store |
| --- | --- | --- |
| **Setting › Style** (`/admin/stylesetting/`) | Site background colour, written into `_variables.scss` under `<instance_path>/data/`. Requires the `update-style-action` permission. | SCSS file on disk |
| **Setting › Site Info** (`/admin/siteinfo/`) | Site name per language, copyright, description, keywords, favicon, login instructions. | `site_info` table |
| **Setting › Search** / **Faceted Search** | Which of the search box, facets, index tree and community blocks are displayed, and the search result layout. | `AdminSettings` |
| **Index Tree › Edit Tree** | Index tree width/height and index link display used by the front page. | `IndexStyle` |
| **Setting › Ranking** | The ranking blocks offered on the front page. | `AdminSettings` |

Instance-level (`invenio.cfg`, rendered from `scripts/instance.cfg`) values that
change the chrome without touching templates:

```python
THEME_SITENAME = 'My Repository'
THEME_SITEURL  = 'https://repo.example.org'
THEME_LOGO       = 'images/my-logo.png'   # under the instance static folder
THEME_LOGO_ADMIN = 'images/my-logo.png'
THEME_INSTITUTION_NAME = {'en': 'My Institution', 'ja': '…'}
THEME_SEARCHBAR = True
DISPLAY_LOGIN = True
```

If you go one step further and override `BASE_PAGE_TEMPLATE`,
`THEME_HEADER_TEMPLATE`, `THEME_FOOTER_TEMPLATE`, `THEME_BODY_TEMPLATE` or
`THEME_FRONTPAGE_TEMPLATE` with your own Jinja templates, you are no longer
doing pure widget customization — see the "template override" section of the
front-end document.

---

## 6. How it is rendered

1. The browser requests a page. Flask renders the theme template
   (`weko_theme/base.html` → `page.html` → `frontpage.html` or the gridlayout
   page template). If a widget design supplies the header/footer, the stock ones
   are emitted hidden.
2. `weko_theme/static/js/weko_theme/widget.js` fetches the design for the
   current page and language from
   `/api/admin/load_widget_design_setting/<lang>` or
   `/api/admin/load_widget_design_page_setting/<page_id>/<lang>` and lays the
   widgets out client-side with gridstack.
3. Dynamic widgets pull their own data afterwards:
   `/api/admin/get_new_arrivals/<widget_id>`,
   `/api/admin/access_counter_record/<repository_id>/<path>/<lang>`,
   `/api/admin/get_page_endpoints/<widget_id>/<lang>`.
4. RSS for the New arrivals widget is served from the `/rss` blueprint.

The admin screens themselves are React + gridstack bundles
(`weko_gridlayout/static/js/weko_gridlayout/widget.design.js` and
`widget.setting.js`).

---

## 7. Caching and troubleshooting

- Design responses are cached (`widget_cache`, `widget_page_cache`) for
  `INVENIO_CACHE_TTL` seconds (50 by default), and compressed when
  `WEKO_GRIDLAYOUT_IS_COMPRESS_WIDGET` is true. **A design change can take up to
  one TTL to appear.** Clear the Redis cache to see it immediately.
- If a new page returns 404, confirm the URL is unique and that it is not
  shadowed by an existing Flask route; the page is registered lazily by the 404
  handler, so the first request after creation is what registers it.
- If a widget cannot be edited, it is locked by another administrator — release
  it from the widget list (`POST /api/admin/widget/unlock`).
- If a rich-text widget shows escaped markup, remember that only the
  `description` and `more_description` fields keep HTML; every other
  multilingual field is HTML-escaped on save.
- Static files return 404 after a fresh install if `invenio widget init` was
  never run.
- Widget height auto-adjustment on the top page is controlled by
  `WEKO_GRIDLAYOUT_AUTO_ADJUST_THE_HEIGHT`.

---

## 8. Checklist

- [ ] Languages registered in **Setting › Language**
- [ ] `invenio widget_type create …` run for all eight types
- [ ] `invenio widget init` run
- [ ] Header / Menu / Main contents / Footer widgets created for `Root Index`
- [ ] Main layout saved in **Page Layout**
- [ ] Extra pages created, with unique URLs, and listed in the Menu widget
- [ ] Site name, logo, favicon and copyright set in **Site Info** / `invenio.cfg`
- [ ] Colours set in **Setting › Style**
- [ ] Verified in every registered language, and per community if used
