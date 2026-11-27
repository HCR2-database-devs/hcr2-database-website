# Prerendering / SSR design note

The app is a client-rendered SPA. `index.html` contains useful metadata, but most
page content is produced only after JavaScript runs. Search engines that do not
execute JavaScript therefore see the shell only.

## Options

| Option | Pros | Cons | Effort |
|---|---|---|---|
| Keep SPA + richer metadata | No build changes; works today | Crawlers still see no page content | Done |
| Build-time prerender of static public routes | Real HTML for home, maps, vehicles, players, tuning pages, records, stats, community, changelog, guidelines, privacy and terms; no runtime server; cheap to host | Needs a build step that renders React with a memory router and writes `dist/<route>/index.html`; data views would need initial data or would still show a client loading state; stale until rebuild | Medium (2–4 days) |
| Full SSR (FastAPI or Node adapter) | Fresh data per request, best metadata and sharing support | New runtime, caching and deployment complexity; backend/frontend teams must coordinate | High (1–3 weeks) |
| Hybrid: prerender static routes, SSR only `/u/:id` and community profiles | Best balance for crawlers and sharing | Two rendering paths to maintain | High |

Prerendering can be added without a large dependency: a small Node script can
import the built app with `react-dom/server`, render each public route with a
`StaticRouter`, inject the result into `dist/index.html`, and write the usual
`dist/<route>/index.html` files. Nginx `try_files` already prefers real files, so
no server change is needed for those routes. Data-heavy pages should either
await their initial query during prerender (which requires build-time database
access) or accept that the prerendered HTML contains only headings and shell
content until hydration.

For true 404 HTTP status codes, a static SPA cannot know whether the browser
requested a valid client route: nginx sees only a path with no file. Either
prerender every valid route (then `try_files ... =404` works) or move route
recognition to the server/SSR layer. Until then, `NotFoundPage` sets a
`noindex` robots meta and a clear title, while nginx returns 200 from the SPA
fallback.

**Recommendation:** prerender the public static routes first. Keep community
profiles as SPA pages, but keep the backend-rendered `/u/:id` share links that
already produce rich Discord embeds. Revisit SSR only if search ranking or
share previews for dynamic profile pages become a business requirement.
