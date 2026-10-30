import { HttpClient } from '@angular/common/http';
import { Injectable, Pipe, PipeTransform, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { Language } from './models';

const STORAGE_KEY = 'language';

/**
 * Traductions partagées avec l'application console : les textes viennent des
 * fichiers locales/*.json, servis par l'API web. Ajouter un fichier de langue
 * l'ajoute aussi au sélecteur de l'interface web.
 */
@Injectable({ providedIn: 'root' })
export class I18n {
  private readonly http = inject(HttpClient);
  private readonly messages = signal<Record<string, string>>({});

  readonly languages = signal<Language[]>([]);
  readonly language = signal('');
  /** Vrai si les traductions n'ont pas pu être chargées (API web arrêtée). */
  readonly unavailable = signal(false);

  async init(): Promise<void> {
    try {
      const languages = await firstValueFrom(this.http.get<Language[]>('/api/languages'));
      this.languages.set(languages);
      const saved = readStorage();
      const code = languages.some((language) => language.code === saved)
        ? saved
        : languages[0]?.code;
      if (code) {
        await this.use(code);
      }
    } catch {
      this.unavailable.set(true);
    }
  }

  async use(code: string): Promise<void> {
    const messages = await firstValueFrom(
      this.http.get<Record<string, string>>(`/api/translations/${code}`),
    );
    this.messages.set(messages);
    this.language.set(code);
    document.documentElement.lang = code;
    writeStorage(code);
  }

  /** Texte de la clé, avec remplacement des paramètres {nom}. Clé inconnue : la clé elle-même. */
  t(key: string, params: Record<string, unknown> = {}): string {
    const text = this.messages()[key] ?? key;
    return text.replace(/\{(\w+)\}/g, (placeholder, name: string) =>
      name in params ? String(params[name]) : placeholder,
    );
  }
}

/** Usage : {{ 'user_not_found' | t: { user_id: 9 } }} */
@Pipe({ name: 't', pure: false })
export class TranslatePipe implements PipeTransform {
  private readonly i18n = inject(I18n);

  transform(key: string, params?: Record<string, unknown>): string {
    return this.i18n.t(key, params);
  }
}

function readStorage(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function writeStorage(code: string): void {
  try {
    localStorage.setItem(STORAGE_KEY, code);
  } catch {
    // Stockage indisponible (navigation privée...) : la langue ne sera simplement pas mémorisée.
  }
}
