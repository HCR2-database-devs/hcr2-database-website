import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";

import { useDialogAccessibility } from "../hooks/useDialogAccessibility";
import { getNews } from "../services/publicData";
import { formatDate } from "../lib/legacyDisplay";
import { FormattedText } from "./FormattedText";

type NewsModalProps = {
  onClose: () => void;
};

export function NewsModal({ onClose }: NewsModalProps) {
  const panelRef = useRef<HTMLDivElement | null>(null);
  const closeRef = useRef<HTMLButtonElement | null>(null);
  useDialogAccessibility({
    open: true,
    onClose,
    containerRef: panelRef,
    initialFocusRef: closeRef,
    modal: true,
    lockScroll: true,
  });

  const news = useQuery({
    queryKey: ["news", 10],
    queryFn: () => getNews(10)
  });

  return (
    <div className="modal-overlay">
      <div
        ref={panelRef}
        className="modal-panel form-container"
        role="dialog"
        aria-modal="true"
        aria-labelledby="news-title"
        tabIndex={-1}
      >
        <h2 id="news-title">Recent News</h2>
        <div id="news-list" className="modal-scroll">
          {news.isLoading && <p role="status">Loading news...</p>}
          {news.isError && <p className="frontend-error" role="alert">Failed to load news.</p>}
          {news.data?.news.length === 0 && <p>No news available.</p>}
          {news.data?.news.map((item) => (
            <div className="news-item" key={item.id}>
              <h3>{item.title}</h3>
              <div className="frontend-muted">
                {formatDate(item.created_at)} - {item.author ?? ""}
              </div>
              <FormattedText text={item.content} />
            </div>
          ))}
        </div>
        <div className="frontend-modal-actions">
          <button ref={closeRef} className="close-news-btn" type="button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
