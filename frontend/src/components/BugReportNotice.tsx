import { DISCORD_INVITE_URL } from "../lib/communityInfo";

type BugReportNoticeProps = {
  className?: string;
};

export function BugReportNotice({ className }: BugReportNoticeProps) {
  return (
    <p className={`bug-report-notice${className ? ` ${className}` : ""}`}>
      <strong>New here, so expect a few bugs.</strong> This section is still being built and tested
      with real players. If something looks wrong or breaks, please report it either by{" "}
      {DISCORD_INVITE_URL ? (
        <>
          <a href={DISCORD_INVITE_URL} target="_blank" rel="noopener noreferrer">
            joining our Discord server
          </a>{" "}
          or{" "}
        </>
      ) : (
        "joining our Discord server or "
      )}
      by using the blue <strong>?</strong> help button in the bottom right corner of the screen.
      Bug reports are very welcome.
    </p>
  );
}