import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { getPublicData } from "../services/publicData";
import { submitPublicRecord } from "../services/submissions";

type PublicSubmitModalProps = {
  onClose: () => void;
};

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
  const maps = useQuery({ queryKey: ["public-data", "maps"], queryFn: () => getPublicData("maps") });
  const vehicles = useQuery({
    queryKey: ["public-data", "vehicles"],
    queryFn: () => getPublicData("vehicles")
  });
  const tuningParts = useQuery({
    queryKey: ["public-data", "tuning-parts"],
    queryFn: () => getPublicData("tuning-parts")
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
          ✕
        </button>
        <h2 id="public-submit-title">Submit a Record (for admin review)</h2>
        <form id="public-submit-form" onSubmit={handleSubmit}>
          <input id="form-load-time" type="hidden" value={formLoadTime} readOnly />
          <label>Map</label>
          <select id="public-map-select" name="mapId" required>
            <option value="">Select a Map</option>
            {(maps.data ?? []).map((map) => (
              <option key={getId(map, "idMap", "idmap")} value={getId(map, "idMap", "idmap")}>
                {getName(map, "nameMap", "namemap")}
              </option>
            ))}
          </select>

          <label>Vehicle</label>
          <select id="public-vehicle-select" name="vehicleId" required>
            <option value="">Select a Vehicle</option>
            {(vehicles.data ?? []).map((vehicle) => (
              <option
                key={getId(vehicle, "idVehicle", "idvehicle")}
                value={getId(vehicle, "idVehicle", "idvehicle")}
              >
                {getName(vehicle, "nameVehicle", "namevehicle")}
              </option>
            ))}
          </select>

          <label>Distance</label>
          <input id="public-distance-input" name="distance" type="number" required min="1" />
          <label>Player Name</label>
          <input id="public-player-name" name="playerName" required />
          <label>Country (optional)</label>
          <input id="public-player-country" name="playerCountry" />

          <label>Tuning Parts (choose 3 or 4)</label>
          <div id="public-tuning-parts" className="frontend-fieldset">
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
                      event.target.checked
                        ? [...current, part.name]
                        : current.filter((item) => item !== part.name)
                    );
                  }}
                />
                {part.name}
              </label>
            ))}
          </div>

          <div style={{ position: "absolute", left: "-9999px", top: "auto", width: 1, height: 1, overflow: "hidden" }}>
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
          <div id="hcaptcha-widget" className="h-captcha" data-sitekey="" />
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
