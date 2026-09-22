import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  ActionRow,
  Container,
  LinkButton,
  Section,
  Separator,
  TextDisplay,
  Thumbnail,
  h,
  toComponentEmbedScript
} from "discord-component-embed";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const indexPath = path.join(root, "index.html");

const card = h(
  Container,
  { accentColor: 0x0f766e },
  h(
    Section,
    {
      accessory: h(Thumbnail, {
        url: "https://hcr2.xyz/img/hcrdatabaselogo.png",
        description: "HCR2 Database logo"
      })
    },
    h(
      TextDisplay,
      null,
      "# HCR2 Database & Records\nCommunity-maintained world records, statistics, and tune-up database for Hill Climb Racing 2."
    ),
    h(TextDisplay, null, "-# Explore the latest world records and site statistics.")
  ),
  h(Separator, { divider: true, spacing: "small" }),
  h(
    ActionRow,
    null,
    h(LinkButton, {
      url: "https://hcr2.xyz/records",
      label: "Records",
      emoji: { name: "🏆" }
    }),
    h(LinkButton, {
      url: "https://hcr2.xyz/stats",
      label: "Stats",
      emoji: { name: "📈" }
    })
  )
);

const tag = toComponentEmbedScript(card);

let html = readFileSync(indexPath, "utf8");
const embedScript =
  /<script id="discord:component-embed" type="application\/json">[\s\S]*?<\/script>\s*/;
if (embedScript.test(html)) {
  html = html.replace(embedScript, "");
}
html = html.replace("</head>", `  ${tag}\n  </head>`);
writeFileSync(indexPath, html);
console.log(`Injected Discord embed (${tag.length} bytes) into ${path.relative(root, indexPath)}`);