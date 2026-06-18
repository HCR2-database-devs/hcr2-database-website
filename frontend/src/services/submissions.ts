import { fetchJson } from "./api";

export type PublicRecordSubmission = {
  mapId: string;
  vehicleId: string;
  distance: string;
  playerName: string;
  playerCountry: string;
  tuningParts: string[];
  echo_affected_part_id: number | null;
  h_captcha_response: string;
  hp_email: string;
  hp_website: string;
  hp_phone: string;
  hp_comments: string;
  form_load_time: number;
  submission_time: number;
};

export function submitPublicRecord(payload: PublicRecordSubmission) {
  return fetchJson<{ success?: boolean; message?: string }>("/api/v1/submissions", {
    method: "POST",
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    }
  });
}
