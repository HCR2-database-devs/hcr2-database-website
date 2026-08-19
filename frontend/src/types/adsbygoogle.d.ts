interface Adsbygoogle {
  push(command: object): void;
}

interface Window {
  adsbygoogle?: Adsbygoogle[];
}
