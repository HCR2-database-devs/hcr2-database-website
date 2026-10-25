const HCAPTCHA_SRC = "https://js.hcaptcha.com/1/api.js";

type HcaptchaOptions = {
  sitekey: string;
  theme?: string;
  callback?: (token: string) => void;
  "expired-callback"?: () => void;
};

declare global {
  interface Window {
    hcaptcha?: {
      render: (container: HTMLElement, options: HcaptchaOptions) => string | number;
      reset?: (widgetId?: string | number) => void;
    };
  }
}

let loaderPromise: Promise<void> | null = null;

export function loadHcaptcha(): Promise<void> {
  if (typeof window === "undefined") {
    return Promise.resolve();
  }
  if (window.hcaptcha) {
    return Promise.resolve();
  }
  if (loaderPromise) {
    return loaderPromise;
  }

  loaderPromise = new Promise<void>((resolve, reject) => {
    const finish = () => resolve();
    const fail = () => {
      loaderPromise = null;
      reject(new Error("Failed to load hCaptcha"));
    };

    const existing = document.querySelector<HTMLScriptElement>("script[data-hcaptcha-loader]");
    if (existing) {
      existing.addEventListener("load", finish, { once: true });
      existing.addEventListener("error", fail, { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = HCAPTCHA_SRC;
    script.async = true;
    script.defer = true;
    script.dataset.hcaptchaLoader = "true";
    script.addEventListener("load", finish, { once: true });
    script.addEventListener("error", fail, { once: true });
    document.head.appendChild(script);
  });

  return loaderPromise;
}
