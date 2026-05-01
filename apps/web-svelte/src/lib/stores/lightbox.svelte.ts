/**
 * Singleton store for the image lightbox. Any component can open the
 * lightbox by calling `lightbox.open({...})` — the host component lives
 * once at the route level and renders based on this store.
 */
export interface LightboxItem {
  src: string;
  alt?: string;
  /** When set, the lightbox shows a "Ir a la página" CTA pointing here. */
  sourceUrl?: string;
  /** Caption shown under the image. */
  caption?: string;
}

class LightboxStore {
  open = $state<LightboxItem | null>(null);

  show(item: LightboxItem): void {
    this.open = item;
  }

  close(): void {
    this.open = null;
  }
}

export const lightbox = new LightboxStore();
