import { HttpClient } from '@angular/common/http';
import { Injectable, Signal, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { FieldDef, RefOption, ResourceSchema } from './models';

/**
 * Description des ressources, fournie par l'API web (resources.py) : les
 * formulaires en sont déduits, les champs ne sont donc définis qu'à un endroit.
 */
@Injectable({ providedIn: 'root' })
export class Schema {
  private readonly http = inject(HttpClient);
  private readonly resources = signal<Record<string, ResourceSchema>>({});
  private readonly optionsCache = new Map<string, Signal<RefOption[]>>();

  async init(): Promise<void> {
    try {
      this.resources.set(
        await firstValueFrom(this.http.get<Record<string, ResourceSchema>>('/api/schema')),
      );
    } catch {
      // API web arrêtée : I18n le signale déjà à l'utilisateur.
    }
  }

  fields(resource: string): FieldDef[] {
    return this.resources()[resource]?.fields ?? [];
  }

  /** Choix possibles pour un champ référence ; chargés une seule fois par ressource. */
  options(resource: string): Signal<RefOption[]> {
    let options = this.optionsCache.get(resource);
    if (!options) {
      const loaded = signal<RefOption[]>([]);
      this.http.get<{ id: number; name?: string; title?: string }[]>(`/api/${resource}`).subscribe({
        next: (items) =>
          loaded.set(items.map((item) => ({ id: item.id, label: item.name ?? item.title ?? '' }))),
        // Pas de signal modifié ici : le prochain affichage retentera le chargement.
        error: () => this.optionsCache.delete(resource),
      });
      options = loaded;
      this.optionsCache.set(resource, options);
    }
    return options;
  }
}
