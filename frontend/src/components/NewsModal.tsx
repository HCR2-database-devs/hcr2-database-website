import { useQuery } from "@tanstack/react-query";

import { getNews } from "../services/publicData";

type NewsModalProps = {
  onClose: () => void;
};

export function NewsModal({ onClose }: NewsModalProps) {
  const news = useQuery({
    queryKey: ["news", 10],
    queryFn: () => getNews(10)
  });

  return (
    <div className="modal-overlay">
      <div className="modal-panel form-container" role="dialog" aria-modal="true" aria-labelledby="news-title">
        <button className="modal-close" type="button" aria-label="Close" onClick={onClose}>
          ✕
        </button>
        <h2 id="news-title">Recent News</h2>
        <div id="news-list" style={{ maxHeight: "60vh", overflow: "auto", textAlign: "left" }}>
          {news.isLoading && <p>Loading news...</p>}
          {news.isError && <p className="frontend-error">Failed to load news.</p>}
          {news.data?.news.length === 0 && <p>No news available.</p>}
          {news.data?.news.map((item) => (
            <div className="news-item" key={item.id}>
              <h3 style={{ margin: "0 0 6px" }}>{item.title}</h3>
              <div className="frontend-muted">
                {item.created_at} — {item.author ?? ""}
              </div>
              <div className="frontend-pre-wrap">{item.content}</div>
            </div>
          ))}
        </div>
        <div className="frontend-modal-actions">
          <button className="close-news-btn" type="button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
