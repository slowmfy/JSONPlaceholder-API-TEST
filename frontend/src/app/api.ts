import { HttpClient, HttpErrorResponse, httpResource } from '@angular/common/http';
import { Injectable, Resource, Signal, computed, inject } from '@angular/core';

import { ApiError, ExplorerResult, UserReport } from './models';

/** Appels propres à certaines pages ; le CRUD des ressources est dans store.ts. */
@Injectable({ providedIn: 'root' })
export class Api {
  private readonly http = inject(HttpClient);

  /** À appeler depuis l'initialisation d'un composant (httpResource). */
  userReport(id: () => string) {
    return httpResource<UserReport>(() => `/api/users/${id()}/report`);
  }

  explore(method: string, path: string, body: unknown) {
    return this.http.post<ExplorerResult>('/api/explorer', { method, path, body });
  }
}

/**
 * Valeur d'une ressource, ou undefined pendant le chargement ou en cas d'erreur
 * (dans ces états, `resource.value()` lève une exception).
 */
export function valueOf<T>(resource: Resource<T>): Signal<T | undefined> {
  return computed(() => (resource.hasValue() ? resource.value() : undefined));
}

/** Convertit n'importe quelle erreur en ApiError affichable. */
export function toApiError(error: unknown): ApiError | null {
  if (!error) {
    return null;
  }
  const body = error instanceof HttpErrorResponse ? error.error : error;
  if (body && typeof body.key === 'string') {
    return { key: body.key, params: body.params ?? {}, field: body.field };
  }
  // Pas de réponse de l'API Python (serveur arrêté, proxy en échec...).
  return { key: 'error_backend_unreachable', params: {} };
}
