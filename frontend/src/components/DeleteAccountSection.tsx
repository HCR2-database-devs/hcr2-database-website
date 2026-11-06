import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { deleteCommunityAccount } from "../services/community";

const CONFIRMATION = "DELETE";

export function DeleteAccountSection() {
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState("");

  const deleteMutation = useMutation({
    mutationFn: deleteCommunityAccount,
    onSuccess: () => {
      window.location.replace("/auth/logout.php");
    },
    onError: (deleteError) => {
      setError(deleteError instanceof Error ? deleteError.message : "Could not delete your account.");
    }
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (confirmation !== CONFIRMATION) {
      setError(`Type ${CONFIRMATION} to confirm.`);
      return;
    }
    setError("");
    deleteMutation.mutate();
  }

  return (
    <section className="account-card delete-account-card">
      <h2>Delete My Data</h2>
      <p>
        This permanently deletes your hcr2.xyz community account, profile, banner, username
        history, notifications, HCR2 verification records, reports involving your account, and
        pending submissions attributed to your account. Approved records for your currently linked
        HCR2 player name are kept, but the link is removed. This cannot be undone.
      </p>
      <p>
        See the <Link to="/privacy">Privacy Policy</Link> for details.
      </p>
      <form className="delete-account-form" onSubmit={handleSubmit}>
        <label htmlFor="delete-account-confirmation">
          Type <strong>{CONFIRMATION}</strong> to confirm
        </label>
        <input
          id="delete-account-confirmation"
          type="text"
          value={confirmation}
          onChange={(event) => setConfirmation(event.target.value)}
          autoComplete="off"
          spellCheck={false}
          disabled={deleteMutation.isPending}
        />
        <button
          className="button delete-account-button"
          type="submit"
          disabled={confirmation !== CONFIRMATION || deleteMutation.isPending}
        >
          {deleteMutation.isPending ? "Deleting..." : "Delete my account and data"}
        </button>
      </form>
      {error && (
        <p className="frontend-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
