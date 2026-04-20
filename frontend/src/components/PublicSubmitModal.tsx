import { useMemo, useState } from "react";
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

  return (
    <div className="modal-overlay" style={{ display: "block" }}>
      <div className="modal-panel form-container" role="dialog" aria-modal="true">
        <button className="modal-close" type="button" aria-label="Close" onClick={onClose}>
          x
        </button>
        <h2>Submit a Record (for admin review)</h2>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            const formData = new FormData(event.currentTarget);
            submit.mutate({
              mapId: String(formData.get("mapId") ?? ""),
              vehicleId: String(formData.get("vehicleId") ?? ""),
              distance: String(formData.get("distance") ?? ""),
              playerName: String(formData.get("playerName") ?? ""),
              playerCountry: String(formData.get("playerCountry") ?? ""),
              tuningParts: selectedParts,
              h_captcha_response: String(formData.get("h_captcha_response") ?? ""),
              hp_email: String(formData.get("hp_email") ?? ""),
              hp_website: String(formData.get("hp_website") ?? ""),
              hp_phone: String(formData.get("hp_phone") ?? ""),
              hp_comments: String(formData.get("hp_comments") ?? ""),
              form_load_time: formLoadTime,
              submission_time: Date.now()
            });
          }}
        >
          <label>Map</label>
          <select name="mapId" required>
            <option value="">Select a Map</option>
            {(maps.data ?? []).map((map) => (
              <option key={getId(map, "idMap", "idmap")} value={getId(map, "idMap", "idmap")}>
                {getName(map, "nameMap", "namemap")}
              </option>
            ))}
          </select>

          <label>Vehicle</label>
          <select name="vehicleId" required>
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
          <input name="distance" type="number" required min="1" />
          <label>Player Name</label>
          <input name="playerName" required />
          <label>Country (optional)</label>
          <input name="playerCountry" />

          <fieldset className="frontend-fieldset">
            <legend>Tuning Parts (choose 3 or 4)</legend>
            {partOptions.map((part) => (
              <label key={part.id}>
                <input
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
          </fieldset>

          <input name="hp_email" className="hp-field" tabIndex={-1} autoComplete="off" />
          <input name="hp_website" className="hp-field" tabIndex={-1} autoComplete="off" />
          <input name="hp_phone" className="hp-field" tabIndex={-1} autoComplete="off" />
          <textarea name="hp_comments" className="hp-field" tabIndex={-1} autoComplete="off" />
          <input name="h_captcha_response" type="hidden" />
          <div id="hcaptcha-widget" className="h-captcha" />

          <button type="submit" disabled={submit.isPending}>
            Submit
          </button>
        </form>
        {message && <p id="public-submit-message">{message}</p>}
      </div>
    </div>
  );
}
