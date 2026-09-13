import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { useBodyScrollLock } from "../hooks/useBodyScrollLock";
import { getHcaptchaSitekey } from "../services/publicData";
import { reportCommunityProfile } from "../services/community";
import type { ReportCategory } from "../types/api";

const REPORT_CATEGORIES: { value: ReportCategory; label: string }[] = [
  { value: "spam", label: "Spam" },
  { value: "inappropriate_banner", label: "Inappropriate banner" },
  { value: "inappropriate_bio", label: "Inappropriate bio" },
  { value: "impersonation", label: "Impersonation" },
  { value: "harassment", label: "Harassment" },
  { value: "other", label: "Other" }
];

type ReportProfileModalProps = {
  profileId: number;
  profileName: string;
  onClose: () => void;
  onReported?: () => void;
};

export function ReportProfileModal({ profileId, profileName, onClose, onReported }: ReportProfileModalProps) {
  useBodyScrollLock();
  const [category, setCategory] = useState<ReportCategory>("other");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const widgetRef = useRef<HTMLDivElement | null>(null);
  const hcaptchaWidgetId = useRef<string | number | null>(null);

  const sitekey = useQuery({
    queryKey: ["hcaptcha-sitekey"],
    queryFn: getHcaptchaSitekey,
    retry: false
  });

  useEffect(() => {
    if (!sitekey.data?.sitekey || !widgetRef.current || hcaptchaWidgetId.current !== null) {
      return undefined;
    }

    const renderWidget = () => {
      if (!widgetRef.current || !window.hcaptcha?.render || !sitekey.data?.sitekey) {
        return false;
      }
      hcaptchaWidgetId.current = window.hcaptcha.render(widgetRef.current, {
        sitekey: sitekey.data.sitekey,
        theme: document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light",
        callback(token) {
          const input = document.getElementById("h-captcha-response") as HTMLInputElement | null;
          if (input) {
            input.value = token;
          }
        },
        "expired-callback"() {
          const input = document.getElementById("h-captcha-response") as HTMLInputElement | null;
          if (input) {
            input.value = "";
          }
        }
      });
      return true;
    };

    if (renderWidget()) {
      return undefined;
    }

    const timer = window.setInterval(() => {
      if (renderWidget()) {
        window.clearInterval(timer);
      }
    }, 200);

    return () => window.clearInterval(timer);
  }, [sitekey.data?.sitekey]);

  const report = useMutation({
    mutationFn: () => {
      const hCaptchaToken = String((document.getElementById("h-captcha-response") as HTMLInputElement | null)?.value ?? "");
      if (!hCaptchaToken) {
        throw new Error("Please complete the hCaptcha verification.");
      }
      return reportCommunityProfile(profileId, category, reason.trim(), hCaptchaToken);
    },
    onSuccess: () => {
      onReported?.();
      onClose();
    },
    onError: (error) => setMessage(error.message)
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!reason.trim()) {
      setMessage("Please describe the issue in a few words.");
      return;
    }
    setMessage("");
    report.mutate();
  }

  return (
    <div className="modal-overlay">
      <div className="modal-panel form-container" role="dialog" aria-modal="true" aria-labelledby="report-profile-title">
        <h2 id="report-profile-title">Report Profile</h2>
        <p className="report-profile-target">Reporting {profileName}</p>
        <form onSubmit={handleSubmit}>
          <label>
            Category
            <select value={category} onChange={(event) => setCategory(event.target.value as ReportCategory)}>
              {REPORT_CATEGORIES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Reason
            <textarea
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              maxLength={500}
              placeholder="What should the moderators review?"
            />
          </label>
          <div id="hcaptcha-widget" ref={widgetRef} className="h-captcha" data-sitekey={sitekey.data?.sitekey ?? ""} />
          {sitekey.isError && <p className="frontend-error">hCaptcha is not configured.</p>}
          <input id="h-captcha-response" name="h_captcha_response" type="hidden" />
          <div className="frontend-modal-actions">
            <button type="submit" disabled={report.isPending}>
              {report.isPending ? "Submitting..." : "Submit Report"}
            </button>
            <button type="button" onClick={onClose}>
              Cancel
            </button>
          </div>
        </form>
        {message && <p className="frontend-error">{message}</p>}
      </div>
    </div>
  );
}