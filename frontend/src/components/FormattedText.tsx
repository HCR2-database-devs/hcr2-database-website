import { Fragment, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { isInternalPath, mentionTarget } from "../lib/contentFormatting";

const CODE = "`(?<code>[^`]+)`";
const LINK = "\\[(?<linkLabel>[^\\]]+)\\]\\((?<linkUrl>[^)\\s]+)\\)";
const MENTION = "\\{\\{\\s*(?<mention>[^{}]+?)\\s*\\}\\}";
const BOLD = "\\*\\*(?<bold>.+?)\\*\\*";
const STRIKE = "~~(?<strike>.+?)~~";
const ITALIC = "\\*(?<italic>.+?)\\*";

const INLINE_RE = new RegExp(`${CODE}|${LINK}|${MENTION}|${BOLD}|${STRIKE}|${ITALIC}`, "g");
const INNER_RE = new RegExp(`${CODE}|${LINK}|${MENTION}|${STRIKE}|${ITALIC}`, "g");

function isSafeExternalUrl(url: string): boolean {
  return /^(https?:|mailto:|tel:)/i.test(url);
}

function linkNode(label: string, url: string, key: string): ReactNode {
  if (isInternalPath(url)) {
    return (
      <Link className="formatted-link formatted-link--internal" to={url} key={key}>
        {renderInner(label)}
      </Link>
    );
  }
  if (isSafeExternalUrl(url)) {
    return (
      <a className="formatted-link formatted-link--external" href={url} target="_blank" rel="noopener noreferrer" key={key}>
        {renderInner(label)}
      </a>
    );
  }
  return <Fragment key={key}>{`[${label}](${url})`}</Fragment>;
}

function mentionNode(raw: string, key: string): ReactNode {
  const to = mentionTarget(raw);
  if (to) {
    return (
      <Link className="formatted-mention" to={to} key={key}>
        {raw.trim()}
      </Link>
    );
  }
  return <Fragment key={key}>{"{{ " + raw.trim() + " }}"}</Fragment>;
}

function tokenize(text: string, re: RegExp, allowBold: boolean): ReactNode[] {
  re.lastIndex = 0;
  const nodes: ReactNode[] = [];
  let lastIndex = 0;
  let counter = 0;
  let match: RegExpExecArray | null;
  while ((match = re.exec(text)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(text.slice(lastIndex, match.index));
    }
    const groups = match.groups ?? {};
    const key = `t-${counter++}`;
    if (groups.code !== undefined) {
      nodes.push(
        <code className="formatted-code" key={key}>
          {groups.code}
        </code>
      );
    } else if (groups.linkLabel !== undefined) {
      nodes.push(linkNode(groups.linkLabel, groups.linkUrl ?? "", key));
    } else if (groups.mention !== undefined) {
      nodes.push(mentionNode(groups.mention, key));
    } else if (allowBold && groups.bold !== undefined) {
      nodes.push(<strong key={key}>{renderInner(groups.bold)}</strong>);
    } else if (groups.strike !== undefined) {
      nodes.push(<del key={key}>{renderInner(groups.strike)}</del>);
    } else if (groups.italic !== undefined) {
      nodes.push(<em key={key}>{renderInner(groups.italic)}</em>);
    }
    lastIndex = re.lastIndex;
  }
  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex));
  }
  return nodes;
}

function renderInline(text: string): ReactNode[] {
  return tokenize(text, INLINE_RE, true);
}

function renderInner(text: string): ReactNode[] {
  return tokenize(text, INNER_RE, false);
}

function renderBlocks(text: string): ReactNode[] {
  const lines = text.split("\n");
  const nodes: ReactNode[] = [];
  let i = 0;
  let counter = 0;

  while (i < lines.length) {
    const trimmed = lines[i].trim();
    if (!trimmed) {
      i += 1;
      continue;
    }
    const key = `b-${counter++}`;

    if (/^-{3,}$/.test(trimmed)) {
      nodes.push(<hr key={key} />);
      i += 1;
      continue;
    }

    const heading = /^(#{1,3})\s+(.*)$/.exec(trimmed);
    if (heading) {
      const tags: Record<number, "h3" | "h4" | "h5"> = { 1: "h3", 2: "h4", 3: "h5" };
      const Tag = tags[heading[1].length];
      nodes.push(<Tag key={key}>{renderInline(heading[2])}</Tag>);
      i += 1;
      continue;
    }

    if (/^[-*]\s/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*]\s/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^[-*]\s/, ""));
        i += 1;
      }
      nodes.push(
        <ul key={key}>
          {items.map((item, index) => (
            <li key={index}>{renderInline(item)}</li>
          ))}
        </ul>
      );
      continue;
    }

    if (/^\d+\.\s/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+\.\s/, ""));
        i += 1;
      }
      nodes.push(
        <ol key={key}>
          {items.map((item, index) => (
            <li key={index}>{renderInline(item)}</li>
          ))}
        </ol>
      );
      continue;
    }

    if (trimmed.startsWith(">")) {
      const quotes: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) {
        quotes.push(lines[i].trim().replace(/^>\s?/, ""));
        i += 1;
      }
      nodes.push(
        <blockquote key={key}>
          {quotes.map((quote, index) => (
            <p key={index}>{renderInline(quote)}</p>
          ))}
        </blockquote>
      );
      continue;
    }

    const paragraph: string[] = [];
    while (i < lines.length) {
      const current = lines[i];
      const currentTrimmed = current.trim();
      if (
        !currentTrimmed ||
        /^(#{1,3})\s+/.test(currentTrimmed) ||
        /^[-*]\s/.test(currentTrimmed) ||
        /^\d+\.\s/.test(currentTrimmed) ||
        /^-{3,}$/.test(currentTrimmed) ||
        currentTrimmed.startsWith(">")
      ) {
        break;
      }
      paragraph.push(current);
      i += 1;
    }
    nodes.push(
      <p key={key}>
        {paragraph.map((para, index) => (
          <Fragment key={index}>
            {renderInline(para)}
            {index < paragraph.length - 1 ? <br /> : null}
          </Fragment>
        ))}
      </p>
    );
  }

  return nodes;
}

type FormattedTextProps = {
  text: string;
  className?: string;
};

export function FormattedText({ text, className }: FormattedTextProps) {
  const classes = ["formatted-text", className].filter(Boolean).join(" ");
  return <div className={classes}>{renderBlocks(text)}</div>;
}