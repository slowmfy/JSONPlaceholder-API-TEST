import { HttpClient, httpResource } from '@angular/common/http';
import { WritableSignal, computed, inject, linkedSignal, signal } from '@angular/core';
import { Observable } from 'rxjs';

import { toApiError } from './api';
import { ApiError, Feedback, Item, WriteResult } from './models';

type Values = Record<string, unknown>;
type Params = Record<string, string | number | boolean>;

/** Ne garde que les champs dont la valeur change : PATCH n'envoie que le nécessaire. */
function changedValues(item: object, values: Values): Values {
  const current = item as Values;
  return Object.fromEntries(
    Object.entries(values).filter(
      ([name, value]) => String(current[name] ?? '') !== String(value ?? ''),
    ),
  );
}

/** Écritures sur une ressource et leur état (en cours, erreur, message de réussite). */
class Writer {
  protected readonly http = inject(HttpClient);
  private readonly resourceName: () => string;

  readonly busy = signal(false);
  readonly error: WritableSignal<ApiError | null>;
  readonly feedback: WritableSignal<Feedback | null>;

  /** `reset` : quand sa valeur change (autre page, autre filtre), les messages sont effacés. */
  constructor(resource: string | (() => string), reset: () => unknown) {
    this.resourceName = typeof resource === 'string' ? () => resource : resource;
    this.error = linkedSignal<unknown, ApiError | null>({ source: reset, computation: () => null });
    this.feedback = linkedSignal<unknown, Feedback | null>({
      source: reset,
      computation: () => null,
    });
  }

  get resource(): string {
    return this.resourceName();
  }

  protected clearMessages(): void {
    this.error.set(null);
    this.feedback.set(null);
  }

  protected run<R>(request: Observable<R>, onSuccess: (result: R) => void): Promise<boolean> {
    this.busy.set(true);
    this.clearMessages();
    return new Promise((resolve) =>
      request.subscribe({
        next: (result) => {
          this.busy.set(false);
          onSuccess(result);
          resolve(true);
        },
        error: (error) => {
          this.busy.set(false);
          this.error.set(toApiError(error));
          resolve(false);
        },
      }),
    );
  }

  protected notify(action: 'created' | 'updated' | 'deleted', id: number): void {
    // posts -> created_post : clés définies dans locales/*.json.
    this.feedback.set({
      key: `${action}_${this.resource.slice(0, -1)}`,
      params: { id },
      simulated: true,
    });
  }

  protected notifyUnchanged(): void {
    this.clearMessages();
    this.feedback.set({ key: 'no_changes', params: {}, simulated: false });
  }
}

/**
 * Liste d'une ressource, modifiable localement. JSONPlaceholder n'enregistre
 * rien : recharger la liste annulerait les écritures, on met donc à jour la
 * copie affichée. À instancier depuis l'initialisation d'un composant.
 */
export class ResourceList<T extends Item> extends Writer {
  readonly source;
  readonly items: WritableSignal<T[]>;
  /** Formulaire ouvert : 'new' pour une création, ou l'élément en cours de modification. */
  readonly editing = signal<'new' | T | null>(null);

  // Les éléments créés n'existent pas sur le serveur : un PATCH ou un DELETE y échouerait.
  private readonly local = new Set<T>();

  constructor(resource: string | (() => string), filters: () => Params | undefined = () => ({})) {
    super(resource, filters);
    this.source = httpResource<T[]>(() => {
      const params = filters();
      return params && { url: `/api/${this.resource}`, params };
    });
    this.items = linkedSignal(() => (this.source.hasValue() ? (this.source.value() ?? []) : []));
  }

  isLocal(item: T): boolean {
    return this.local.has(item);
  }

  /** Ouvre ('new' ou un élément) ou ferme (null) le formulaire. */
  edit(target: 'new' | T | null): void {
    this.editing.set(target);
    this.clearMessages();
  }

  async save(values: Values): Promise<void> {
    const target = this.editing();
    if (target) {
      const saved = await (target === 'new' ? this.create(values) : this.update(target, values));
      if (saved) {
        this.editing.set(null);
      }
    }
  }

  create(values: Values): Promise<boolean> {
    return this.run(this.http.post<WriteResult<T>>(`/api/${this.resource}`, values), ({ item }) => {
      this.local.add(item);
      this.items.update((items) => [item, ...items]);
      this.notify('created', item.id);
    });
  }

  update(item: T, values: Values): Promise<boolean> {
    const changes = changedValues(item, values);
    if (Object.keys(changes).length === 0) {
      this.notifyUnchanged();
      return Promise.resolve(true);
    }
    if (this.isLocal(item)) {
      this.clearMessages();
      this.replace(item, { ...item, ...changes });
      this.notify('updated', item.id);
      return Promise.resolve(true);
    }
    return this.run(
      this.http.patch<WriteResult<T>>(`/api/${this.resource}/${item.id}`, changes),
      (result) => {
        this.replace(item, result.item);
        this.notify('updated', item.id);
      },
    );
  }

  remove(item: T): Promise<boolean> {
    if (this.isLocal(item)) {
      this.clearMessages();
      this.drop(item);
      return Promise.resolve(true);
    }
    return this.run(this.http.delete(`/api/${this.resource}/${item.id}`), () => this.drop(item));
  }

  private replace(item: T, updated: T): void {
    if (this.local.delete(item)) {
      this.local.add(updated);
    }
    this.items.update((items) => items.map((current) => (current === item ? updated : current)));
  }

  private drop(item: T): void {
    this.local.delete(item);
    this.items.update((items) => items.filter((current) => current !== item));
    this.notify('deleted', item.id);
  }
}

/** Un élément d'une ressource (pages de détail). */
export class ResourceItem<T extends Item> extends Writer {
  readonly source;
  readonly value: WritableSignal<T | undefined>;
  readonly deleted: WritableSignal<boolean>;
  readonly editing: WritableSignal<boolean>;
  readonly exists = computed(() => !this.deleted() && this.value() !== undefined);

  constructor(resource: string, id: () => string | number | undefined) {
    super(resource, id);
    this.source = httpResource<T>(() => (id() ? `/api/${resource}/${id()}` : undefined));
    this.value = linkedSignal(() => (this.source.hasValue() ? this.source.value() : undefined));
    this.deleted = linkedSignal<unknown, boolean>({ source: id, computation: () => false });
    this.editing = linkedSignal<unknown, boolean>({ source: id, computation: () => false });
  }

  /** Ouvre ou ferme le formulaire de modification. */
  edit(open: boolean): void {
    this.editing.set(open);
    this.clearMessages();
  }

  async save(values: Values): Promise<void> {
    const item = this.value();
    if (!item) {
      return;
    }
    const changes = changedValues(item, values);
    if (Object.keys(changes).length === 0) {
      this.editing.set(false);
      this.notifyUnchanged();
      return;
    }
    const saved = await this.run(
      this.http.patch<WriteResult<T>>(`/api/${this.resource}/${item.id}`, changes),
      (result) => {
        this.value.set(result.item);
        this.notify('updated', item.id);
      },
    );
    if (saved) {
      this.editing.set(false);
    }
  }

  remove(): Promise<boolean> {
    const item = this.value();
    if (!item) {
      return Promise.resolve(false);
    }
    return this.run(this.http.delete(`/api/${this.resource}/${item.id}`), () => {
      this.deleted.set(true);
      this.notify('deleted', item.id);
    });
  }
}
