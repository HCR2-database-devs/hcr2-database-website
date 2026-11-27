import { CookieSettings } from "../components/CookieSettings";

export function PrivacyPage() {
  return (
    <main className="standalone-page">
      <div className="policy-container">
        <h1>Privacy Policy</h1>
        <p><strong>Effective Date: 27 November 2026</strong></p>

        <h2>Introduction</h2>
        <p>
          HCR2 Records respects your privacy. This Privacy Policy explains what information we
          collect, how we use it, how long we keep it, and the choices available to you when you use
          hcr2.xyz.
        </p>
        <p>
          By using this website, you agree to the practices described in this Privacy Policy. If you
          do not agree, please do not use the website.
        </p>

        <h2>Information We Collect</h2>

        <h3>Record submissions</h3>
        <p>
          When you submit a record, we collect the information needed to review and publish it:
        </p>
        <ul>
          <li>Player name, map, vehicle, distance, and tuning parts</li>
          <li>Optional country and echo-affected tuning part</li>
          <li>The submission status and moderation history</li>
          <li>An hCaptcha verification response, used to check that the submission is not automated</li>
        </ul>
        <p>
          If you are signed in to a community account, the submission is linked to that account. If
          you submit while signed out, we store the submitting IP address instead. Authenticated
          submissions do not store the submitting IP address on the submission itself.
        </p>
        <p>
          Approved records, including the player name, map, vehicle, distance, country, and tuning
          information, are displayed publicly and may remain in the shared records database.
        </p>

        <h3>Community accounts</h3>
        <p>
          When you sign in with Discord, our authentication service at auth.hcr2.xyz receives your
          Discord user ID, Discord username, and Discord avatar. A community account record may be
          created automatically. You choose a public community username before your profile appears
          in the member directory.
        </p>
        <p>We store the community information you provide or choose to display, such as:</p>
        <ul>
          <li>Your community username and a history of previous usernames</li>
          <li>Profile bio, country, favorite vehicle, and favorite map</li>
          <li>Profile visibility settings</li>
          <li>Discord username and avatar, if you choose to display them</li>
          <li>A custom profile banner image, if you upload one</li>
          <li>Notifications sent to you about account and moderation actions</li>
        </ul>

        <h3>HCR2 account linking</h3>
        <p>
          If you request an HCR2 player-name link, we store the player name you select, the
          verification method, verification codes or challenge details, the steps you confirm, and
          the administrator&apos;s decision and notes. A verified link is shown on your profile
          according to your visibility settings.
        </p>

        <h3>Reports and moderation</h3>
        <p>
          When a community profile is reported, we store the reporter&apos;s account identity, the
          reported profile, the report category, the explanation, the status, and administrative
          notes. This information is used to review and resolve reports. Administrators may also
          record moderation actions, including changed usernames, disabled profiles, and related
          reasons.
        </p>

        <h3>IP addresses and anti-abuse data</h3>
        <p>
          We process IP addresses to verify hCaptcha responses, enforce submission rate limits,
          detect abuse, and apply IP bans. For signed-out record submissions, the IP address is stored
          with the pending submission. It is cleared when the submission is accepted or declined. A
          pending submission that is never moderated may keep its IP address until it is reviewed or
          removed.
        </p>
        <p>
          When an IP address is banned, we store the banned IP address, the reason, the administrator
          who issued the ban, the creation date, the optional expiry date, and whether the ban is
          active. Active bans are used to block submissions. Expired or lifted ban records, and
          administrative activity logs that may include the banned IP address and ban action, may be
          retained in administrative records until they are removed by administrators. Contact us if
          you want a ban record reviewed for removal.
        </p>
        <p>
          Submission rate-limit counters use a keyed hash of an IP address or account identifier
          rather than the raw value when the service is configured to do so. These counters are used
          only to limit abuse and may be removed during maintenance.
        </p>

        <h3>Browser storage and cookies</h3>
        <p>
          The site uses one essential authentication cookie, <code>WC_TOKEN</code>. It is set by our
          auth.hcr2.xyz login service, is HttpOnly, Secure and SameSite=Lax, and cannot be read by
          JavaScript. It is cleared when you sign out or delete your account. It is exempt from the
          advertising choice below because sign-in cannot work without it.
        </p>
        <p>We use the following browser storage keys:</p>
        <ul>
          <li>
            <code>darkMode</code> (localStorage) — your light/dark theme preference.
          </li>
          <li>
            <code>hcr2-consent</code> (localStorage) — your advertising choice and the time it was
            made. No advertising script loads before you choose.
          </li>
          <li>
            <code>announcement:community-launch-2026-10:logged-in</code> (localStorage) and
            <code> announcement:community-launch-2026-10:logged-out</code> (sessionStorage) — whether
            you dismissed the community announcement.
          </li>
          <li>
            <code>hcr2-scroll-positions</code> (sessionStorage) — scroll positions while you browse.
          </li>
          <li>
            <code>hcr2-adblock-notice-dismissed</code> (sessionStorage) — whether you dismissed the
            optional ad-block notice.
          </li>
        </ul>
        <p>
          hCaptcha is loaded only when you open the record submission or profile report form. It is
          needed to protect those forms from automated abuse and may process your IP address, browser
          information and interaction signals under its own policy.
        </p>

        <h2 id="cookie-settings">Cookie settings</h2>
        <p>
          Advertising is off by default. If you accept, Google AdSense and its partners may set
          cookies or similar identifiers to serve and measure ads. If you reject, the AdSense script
          is not loaded. Crawlers and visitors who request reduced data do not see ads or the
          ad-block notice. You can change your choice below at any time.
        </p>
        <CookieSettings />

        <h2>How We Use Information</h2>
        <ul>
          <li>Review, verify, and publish record submissions</li>
          <li>Operate community accounts, profiles, notifications, and HCR2 account linking</li>
          <li>Moderate reports and enforce community rules</li>
          <li>Prevent spam, automated submissions, ban evasion, and other abuse</li>
          <li>Authenticate users and maintain secure sessions</li>
          <li>Operate, maintain, and improve the reliability of the website</li>
          <li>Comply with legal obligations and respond to lawful requests</li>
        </ul>
        <p>We do not sell or rent personal information, and we do not share it for third-party marketing.</p>

        <h2>Public Information</h2>
        <p>
          Approved records and the public parts of community profiles are visible to anyone. Your
          profile visibility settings control fields such as your bio, country, favorite vehicle,
          favorite map, Discord username, Discord avatar, and linked HCR2 player name.
        </p>
        <p>
          Even if you hide a field on your profile, approved records and other information you
          submitted may still be public in the records database where it is not linked to your
          community account.
        </p>

        <h2>Third-Party Services</h2>
        <p>We use the following third-party services:</p>
        <ul>
          <li>
            <strong>Discord</strong> for optional sign-in through Discord OAuth. Discord processes
            your login and account information under its own privacy policy. Authentication is
            handled by our auth.hcr2.xyz service. See{" "}
            <a href="https://discord.com/privacy" target="_blank" rel="noopener noreferrer">
              Discord&apos;s Privacy Policy
            </a>
            .
          </li>
          <li>
            <strong>hCaptcha</strong> to protect submissions and reports from automated abuse.
            hCaptcha may process your IP address, browser information, and interaction signals. See{" "}
            <a href="https://www.hcaptcha.com/privacy" target="_blank" rel="noopener noreferrer">
              hCaptcha&apos;s Privacy Policy
            </a>
            .
          </li>
          <li>
            <strong>Google AdSense</strong> for advertising only when ads are enabled and you have
            accepted ads. The AdSense script is not loaded before that choice. Google and its
            partners may use cookies or similar technologies to serve and measure ads. See{" "}
            <a href="https://policies.google.com/technologies/ads" target="_blank" rel="noopener noreferrer">
              How Google uses information for ads
            </a>{" "}
            and the{" "}
            <a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer">
              Google Privacy Policy
            </a>
            .
          </li>
          <li>
            <strong>Discord&apos;s CDN (cdn.discordapp.com)</strong> for optional community profile
            avatars. The browser requests those images directly from Discord when a profile with an
            avatar is shown. We do not send your profile data to Discord through that request beyond
            the normal information a browser sends when loading an image.
          </li>
          <li>
            <strong>flagcdn.com</strong> for small country flag images. The browser requests those
            images directly from FlagCDN when a country is shown; no script or cookie is loaded from
            that host by this site.
          </li>
        </ul>
        <p>
          These services operate under their own privacy policies and terms. We encourage you to
          review those policies before using the associated features.
        </p>

        <h2>Data Storage and Security</h2>
        <p>
          Website data is stored in a database and protected using administrative and technical
          safeguards. We take reasonable measures to protect information from unauthorized access,
          misuse, alteration, or disclosure.
        </p>
        <p>
          No internet service can guarantee absolute security. If you believe your account or data
          has been compromised, contact us.
        </p>

        <h2>Data Retention</h2>
        <ul>
          <li>
            Approved records and public profile content may remain on the website until removed by
            administrators or through account deletion.
          </li>
          <li>
            Pending and rejected submissions may be retained for moderation, abuse prevention, and
            database maintenance.
          </li>
          <li>
            Signed-out submission IP addresses are cleared when the submission is accepted or
            declined. They may remain while a submission is pending.
          </li>
          <li>
            IP ban records and related administrative activity logs may remain after a ban expires
            or is lifted until an administrator removes them.
          </li>
          <li>
            Community account data, notifications, reports, HCR2 linking records, and attributed
            submissions are retained until you delete your account or an administrator removes them.
          </li>
          <li>
            Rate-limit counters and other anti-abuse records are retained only as long as needed for
            rate limiting and maintenance.
          </li>
          <li>
            Authentication session data is retained only as long as needed to keep you securely
            signed in.
          </li>
        </ul>

        <h2>Deleting Your Account and Data</h2>
        <p>
          If you have a community account, you can delete it from your{" "}
          <a href="/account">Account page</a>. Sign in, open the Delete My Data section, and type the
          requested confirmation. Deletion is immediate and cannot be undone.
        </p>
        <p>Deleting your account removes:</p>
        <ul>
          <li>Your community account, profile, banner, and visibility settings</li>
          <li>Your username history, notifications, and feature-testing records</li>
          <li>Your HCR2 account link and HCR2 verification request data</li>
          <li>Reports involving your account</li>
          <li>Pending submissions attributed to your account</li>
          <li>Your active login session cookie</li>
        </ul>
        <p>Account deletion does not remove:</p>
        <ul>
          <li>Active or historical IP ban records and administrative activity logs</li>
          <li>Approved records for your currently linked HCR2 player name; only the link is removed</li>
          <li>Signed-out submissions that are not linked to your account</li>
          <li>Public player names or records that are not attributed to your community account</li>
          <li>Copies of public content that other people or services may have saved</li>
          <li>Aggregated or derived information that no longer identifies you</li>
        </ul>
        <p>
          If you sign in again after deleting your account, a new community account may be created.
          Your old profile and deleted data will not be restored.
        </p>
        <p>
          You may also contact us to request access, correction, or removal of other personal
          information where applicable.
        </p>

        <h2>Children&apos;s Privacy</h2>
        <p>
          This website is not intended for children under the age of 13. We do not knowingly collect
          personal information from children under 13.
        </p>
        <p>
          If you believe a child has submitted personal information through this website, please
          contact us so the information can be removed.
        </p>

        <h2>Your Rights</h2>
        <p>
          Depending on where you live, you may have rights to access, correct, delete, restrict, or
          object to the processing of your personal information. You can use the account deletion
          tool for community account data, and you can contact us for other requests.
        </p>
        <p>
          We may need to verify your identity before fulfilling a request, and we may retain
          information where required by law or needed to prevent abuse.
        </p>
        <p>
          For privacy-related requests or questions, please contact:
        </p>
        <p>
          <strong>Email:</strong>{" "}
          <a href="mailto:nipatsuplaying@gmail.com">nipatsuplaying@gmail.com</a>
        </p>

        <h2>Changes to This Policy</h2>
        <p>
          This Privacy Policy may be updated to reflect changes to the website, our data practices,
          or legal requirements. The effective date at the top of this page indicates the most recent
          revision.
        </p>

        <p>
          <a href="/terms">See our Terms of Service</a>
        </p>

        <p className="policy-note">
          <strong>Last updated: 27 November 2026</strong>
        </p>
        <p>
          <a href="/">Back to site</a>
        </p>
      </div>
    </main>
  );
}
