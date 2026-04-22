import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { getHcaptchaSitekey, getPublicData } from "../services/publicData";
import { submitPublicRecord } from "../services/submissions";

type PublicSubmitModalProps = {
  onClose: () => void;
};

declare global {
  interface Window {
    hcaptcha?: {
      render: (
        container: HTMLElement,
        options: {
          sitekey: string;
          theme?: string;
          callback?: (token: string) => void;
          "expired-callback"?: () => void;
        }
      ) => string | number;
      reset?: (widgetId?: string | number) => void;
    };
  }
}

function getId(row: Record<string, unknown>, camel: string, lower: string) {
  return String(row[camel] ?? row[lower] ?? "");
}

function getName(row: Record<string, unknown>, camel: string, lower: string) {
  return String(row[camel] ?? row[lower] ?? "");
}

export function PublicSubmitModal({ onClose }: PublicSubmitModalProps) {
  const [selectedParts, setSelectedParts] = useState<string[]>([]);
  const [message, setMessage] = useState<string>("");
  const [formLoadTime] = useState(() => Date.now());
  const widgetRef = useRef<HTMLDivElement | null>(null);
  const hcaptchaWidgetId = useRef<string | number | null>(null);
  const maps = useQuery({ queryKey: ["public-data", "maps"], queryFn: () => getPublicData("maps") });
  const vehicles = useQuery({
    queryKey: ["public-data", "vehicles"],
    queryFn: () => getPublicData("vehicles")
  });
  const tuningParts = useQuery({
    queryKey: ["public-data", "tuning-parts"],
    queryFn: () => getPublicData("tuning-parts")
  });
  const sitekey = useQuery({
    queryKey: ["hcaptcha-sitekey"],
    queryFn: getHcaptchaSitekey,
    retry: false
  });

  const submit = useMutation({
    mutationFn: submitPublicRecord,
    onSuccess: (result) => setMessage(result.message ?? "Submission received."),
    onError: (error) => setMessage(error.message)
  });

  const partOptions = useMemo(
    () =>
      (tuningParts.data ?? []).map((part) => ({
        id: getId(part, "idTuningPart", "idtuningpart"),
        name: getName(part, "nameTuningPart", "nametuningpart")
      })),
    [tuningParts.data]
  );

  useEffect(() => {
    if (!sitekey.data?.sitekey || !widgetRef.current || hcaptchaWidgetId.current !== null) {
      return undefined;
    }

    let attempts = 0;
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
      attempts += 1;
      if (renderWidget() || attempts >= 30) {
        window.clearInterval(timer);
      }
    }, 200);

    return () => window.clearInterval(timer);
  }, [sitekey.data?.sitekey]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const mapId = String(formData.get("mapId") ?? "");
    const vehicleId = String(formData.get("vehicleId") ?? "");
    const distance = String(formData.get("distance") ?? "");
    const playerName = String(formData.get("playerName") ?? "").trim();
    const hcaptchaResponse = String(formData.get("h_captcha_response") ?? "");

    if (!mapId || !vehicleId || !distance || !playerName) {
      setMessage("Please complete all required fields.");
      return;
    }
    if (Number.isNaN(Number(distance)) || Number(distance) <= 0) {
      setMessage("Distance must be a positive number.");
      return;
    }
    if (selectedParts.length < 3 || selectedParts.length > 4) {
      setMessage("Please choose 3 or 4 tuning parts for the record.");
      return;
    }
    if (!hcaptchaResponse) {
      setMessage("Please complete the hCaptcha verification.");
      return;
    }

    submit.mutate({
      mapId,
      vehicleId,
      distance,
      playerName,
      playerCountry: String(formData.get("playerCountry") ?? ""),
      tuningParts: selectedParts,
      h_captcha_response: hcaptchaResponse,
      hp_email: String(formData.get("hp_email") ?? ""),
      hp_website: String(formData.get("hp_website") ?? ""),
      hp_phone: String(formData.get("hp_phone") ?? ""),
      hp_comments: String(formData.get("hp_comments") ?? ""),
      form_load_time: formLoadTime,
      submission_time: Date.now()
    });
  }

  return (
    <div id="public-submit-overlay" className="modal-overlay">
      <div className="modal-panel form-container" role="dialog" aria-modal="true" aria-labelledby="public-submit-title">
        <button className="modal-close" type="button" aria-label="Close" onClick={onClose}>
          Close
        </button>
        <h2 id="public-submit-title">Submit a Record (for admin review)</h2>
        <form id="public-submit-form" onSubmit={handleSubmit}>
          <input id="form-load-time" type="hidden" value={formLoadTime} readOnly />
          <label>
            Map
            <select id="public-map-select" name="mapId" required>
              <option value="">Select a Map</option>
              {(maps.data ?? []).map((map) => (
                <option key={getId(map, "idMap", "idmap")} value={getId(map, "idMap", "idmap")}>
                  {getName(map, "nameMap", "namemap")}
                </option>
              ))}
            </select>
          </label>

          <label>
            Vehicle
            <select id="public-vehicle-select" name="vehicleId" required>
              <option value="">Select a Vehicle</option>
              {(vehicles.data ?? []).map((vehicle) => (
                <option key={getId(vehicle, "idVehicle", "idvehicle")} value={getId(vehicle, "idVehicle", "idvehicle")}>
                  {getName(vehicle, "nameVehicle", "namevehicle")}
                </option>
              ))}
            </select>
          </label>

          <label>
            Distance
            <input id="public-distance-input" name="distance" type="number" required min="1" />
          </label>
          <label>
            Player Name
            <input id="public-player-name" name="playerName" required />
          </label>
          <label>
            Country (optional)
            <input id="public-player-country" name="playerCountry" />
          </label>

          <fieldset id="public-tuning-parts" className="frontend-fieldset">
            <legend>Tuning Parts (choose 3 or 4)</legend>
            {partOptions.map((part) => (
              <label key={part.id}>
                <input
                  id={`public-tuning-part-${part.id}`}
                  name="public-tuning-part"
                  type="checkbox"
                  value={part.name}
                  checked={selectedParts.includes(part.name)}
                  onChange={(event) => {
                    setSelectedParts((current) =>
                      event.target.checked ? [...current, part.name] : current.filter((item) => item !== part.name)
                    );
                  }}
                />
                {part.name}
              </label>
            ))}
          </fieldset>

          <div className="hp-field" aria-hidden="true">
            <label>
              Email
              <input id="hp_email" name="hp_email" tabIndex={-1} autoComplete="off" />
            </label>
            <label>
              Website
              <input id="hp_website" name="hp_website" tabIndex={-1} autoComplete="off" />
            </label>
            <label>
              Phone
              <input id="hp_phone" name="hp_phone" tabIndex={-1} autoComplete="off" />
            </label>
            <label>
              Comments
              <textarea id="hp_comments" name="hp_comments" tabIndex={-1} autoComplete="off" />
            </label>
          </div>
          <div id="hcaptcha-widget" ref={widgetRef} className="h-captcha" data-sitekey={sitekey.data?.sitekey ?? ""} />
          {sitekey.isError && <p className="frontend-error">hCaptcha is not configured.</p>}
          <input id="h-captcha-response" name="h_captcha_response" type="hidden" />

          <div className="frontend-modal-actions">
            <button type="submit" disabled={submit.isPending}>
              Send Submission
            </button>
            <button type="button" onClick={onClose}>
              Cancel
            </button>
          </div>
        </form>
        {message && <p id="public-submit-message">{message}</p>}
      </div>
    </div>
  );
}
