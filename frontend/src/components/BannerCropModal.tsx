import { useEffect, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";

import { useBodyScrollLock } from "../hooks/useBodyScrollLock";

const BANNER_RATIO = 3.6;
const MAX_ZOOM_MULTIPLIER = 8;

type BannerCropModalProps = {
  file: File;
  aspectRatio?: number;
  onConfirm: (file: File) => void;
  onCancel: () => void;
};

export function BannerCropModal({
  file,
  aspectRatio = BANNER_RATIO,
  onConfirm,
  onCancel
}: BannerCropModalProps) {
  useBodyScrollLock();

  const containerRef = useRef<HTMLDivElement | null>(null);
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [applied, setApplied] = useState<{
    scale: number;
    imgLeft: number;
    imgTop: number;
  } | null>(null);
  const dragRef = useRef<{ x: number; y: number } | null>(null);
  const [dragging, setDragging] = useState(false);

  useEffect(() => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      setImage(img);
      setApplied(null);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
    };
    img.src = url;
    return () => {
      URL.revokeObjectURL(url);
    };
  }, [file]);

  const rect = containerRef.current?.getBoundingClientRect();
  const containerWidth = rect?.width ?? 0;
  const containerHeight = rect?.height ?? 0;
  const winWidth = Math.min(containerWidth, containerHeight * aspectRatio);
  const winHeight = winWidth / aspectRatio;
  const windowBox =
    winWidth === 0
      ? null
      : {
          x: (containerWidth - winWidth) / 2,
          y: (containerHeight - winHeight) / 2,
          width: winWidth,
          height: winHeight,
        };

  const naturalWidth = image?.naturalWidth ?? 0;
  const naturalHeight = image?.naturalHeight ?? 0;
  const minScale =
    windowBox && naturalWidth > 0 && naturalHeight > 0
      ? Math.max(windowBox.width / naturalWidth, windowBox.height / naturalHeight)
      : 1;
  const maxScale = Math.max(
    minScale,
    2000 / Math.max(naturalWidth, naturalHeight, 1),
  );

  function clampState(scale: number, imgLeft: number, imgTop: number) {
    if (!windowBox || naturalWidth === 0 || naturalHeight === 0) {
      return { scale, imgLeft, imgTop };
    }
    const imageWidth = naturalWidth * scale;
    const imageHeight = naturalHeight * scale;
    const minLeft = windowBox.x + windowBox.width - imageWidth;
    const maxLeft = windowBox.x;
    const minTop = windowBox.y + windowBox.height - imageHeight;
    const maxTop = windowBox.y;
    return {
      scale: Math.max(minScale, Math.min(maxScale, scale)),
      imgLeft: Math.max(minLeft, Math.min(maxLeft, imgLeft)),
      imgTop: Math.max(minTop, Math.min(maxTop, imgTop)),
    };
  }

  function initialFit() {
    if (!windowBox || naturalWidth === 0) return clampState(1, 0, 0);
    const cover = minScale;
    return clampState(
      cover,
      windowBox.x + (windowBox.width - naturalWidth * cover) / 2,
      windowBox.y + (windowBox.height - naturalHeight * cover) / 2,
    );
  }

  function zoomAt(factor: number) {
    setApplied((current) => {
      if (!current || !windowBox) return current;
      const centerX = windowBox.x + windowBox.width / 2;
      const centerY = windowBox.y + windowBox.height / 2;
      const nextScale = current.scale * factor;
      return clampState(
        nextScale,
        centerX - (centerX - current.imgLeft) * (nextScale / current.scale),
        centerY - (centerY - current.imgTop) * (nextScale / current.scale),
      );
    });
  }

  useEffect(() => {
    if (applied || !image) return;
    setApplied(initialFit());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [image, applied]);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      zoomAt(event.deltaY < 0 ? 1.12 : 1 / 1.12);
    };
    element.addEventListener("wheel", onWheel, { passive: false });
    return () => element.removeEventListener("wheel", onWheel);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [image]);

  if (!image) {
    return (
      <div id="banner-crop-overlay" className="modal-overlay">
        <div className="modal-panel form-container">
          <h2>Preparing banner…</h2>
        </div>
      </div>
    );
  }

  function handlePointerDown(event: ReactPointerEvent) {
    (event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId);
    dragRef.current = { x: event.clientX, y: event.clientY };
    setDragging(true);
  }

  function handlePointerMove(event: ReactPointerEvent) {
    const start = dragRef.current;
    if (!start || !applied) return;
    const dx = event.clientX - start.x;
    const dy = event.clientY - start.y;
    dragRef.current = { x: event.clientX, y: event.clientY };
    setApplied(
      clampState(applied.scale, applied.imgLeft + dx, applied.imgTop + dy),
    );
  }

  function handlePointerUp(event: ReactPointerEvent) {
    (event.currentTarget as HTMLElement).releasePointerCapture?.(event.pointerId);
    dragRef.current = null;
    setDragging(false);
  }

  async function handleConfirm() {
    if (!image || !applied || !windowBox) return;
    const naturalX = (windowBox.x - applied.imgLeft) / applied.scale;
    const naturalY = (windowBox.y - applied.imgTop) / applied.scale;
    const cropWidth = windowBox.width / applied.scale;
    const cropHeight = windowBox.height / applied.scale;
    const safeX = Math.max(0, Math.min(naturalWidth - cropWidth, naturalX));
    const safeY = Math.max(0, Math.min(naturalHeight - cropHeight, naturalY));

    const outputWidth = Math.max(1, Math.round(Math.min(2048, cropWidth)));
    const outputHeight = Math.max(1, Math.round(outputWidth / aspectRatio));

    const canvas = document.createElement("canvas");
    canvas.width = outputWidth;
    canvas.height = outputHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      onCancel();
      return;
    }
    ctx.drawImage(
      image,
      safeX,
      safeY,
      cropWidth,
      cropHeight,
      0,
      0,
      outputWidth,
      outputHeight,
    );
    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, "image/webp", 0.85),
    );
    if (!blob) {
      onCancel();
      return;
    }
    const name = file.name.replace(/\.[^.]+$/, "") + ".webp";
    onConfirm(new File([blob], name, { type: "image/webp" }));
  }

  const previewStyle = applied
    ? {
        width: naturalWidth * applied.scale,
        height: naturalHeight * applied.scale,
        left: applied.imgLeft,
        top: applied.imgTop,
      }
    : undefined;

  return (
    <div id="banner-crop-overlay" className="modal-overlay">
      <div
        className="modal-panel form-container banner-crop-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="banner-crop-title"
      >
        <h2 id="banner-crop-title">Crop your banner</h2>
        <p className="banner-crop-hint">
          Drag to position, scroll or use the buttons to zoom. The highlighted
          area is what visitors see.
        </p>
        <div
          ref={containerRef}
          className="banner-crop-stage"
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
        >
          {previewStyle && (
            <img
              className="banner-crop-image"
              src={image.src}
              alt=""
              draggable={false}
              style={{ position: "absolute", maxWidth: "none", ...previewStyle }}
            />
          )}
          <div
            className={`banner-crop-window${dragging ? " banner-crop-window--active" : ""}`}
            style={windowBox ? { width: windowBox.width, height: windowBox.height } : undefined}
            aria-hidden="true"
          />
        </div>
        <div className="banner-crop-controls">
          <button type="button" className="button-ghost" onClick={() => zoomAt(1.25)}>
            +
          </button>
          <button type="button" className="button-ghost" onClick={() => zoomAt(1 / 1.25)}>
            −
          </button>
          <button type="button" className="button-ghost" onClick={() => setApplied(initialFit())}>
            Reset
          </button>
        </div>
        <div className="frontend-modal-actions">
          <button type="button" className="button-ghost" onClick={onCancel}>
            Cancel
          </button>
          <button type="button" className="button-ghost" onClick={() => onConfirm(file)}>
            Use without cropping
          </button>
          <button type="button" onClick={handleConfirm}>
            Apply &amp; upload
          </button>
        </div>
      </div>
    </div>
  );
}