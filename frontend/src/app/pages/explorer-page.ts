import { Component, computed, inject, signal } from '@angular/core';

import { Api, toApiError } from '../api';
import { TranslatePipe } from '../i18n';
import { ApiError, ExplorerResult } from '../models';

const BASE_URL = 'https://jsonplaceholder.typicode.com';
const WITH_BODY = ['POST', 'PUT', 'PATCH'];
const POST_BODY = JSON.stringify({ userId: 1, title: 'foo', body: 'bar' }, null, 2);
const PUT_BODY = JSON.stringify({ id: 1, userId: 1, title: 'foo', body: 'bar' }, null, 2);

interface Example {
  method: string;
  path: string;
  body?: string;
}

/** Couvre toutes les routes de JSONPlaceholder, y compris celles sans écran dédié. */
@Component({
  selector: 'app-explorer-page',
  imports: [TranslatePipe],
  templateUrl: './explorer-page.html',
})
export class ExplorerPage {
  private readonly api = inject(Api);

  protected readonly methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'];
  protected readonly examples: Example[] = [
    { method: 'GET', path: '/users' },
    { method: 'GET', path: '/posts?userId=1' },
    { method: 'GET', path: '/posts/1/comments' },
    { method: 'GET', path: '/users/1/todos' },
    { method: 'GET', path: '/albums/1/photos' },
    { method: 'GET', path: '/todos?completed=true' },
    { method: 'POST', path: '/posts', body: POST_BODY },
    { method: 'PUT', path: '/posts/1', body: PUT_BODY },
    { method: 'PATCH', path: '/todos/1', body: JSON.stringify({ completed: true }, null, 2) },
    { method: 'DELETE', path: '/posts/1' },
  ];

  protected readonly method = signal('GET');
  protected readonly path = signal('/users');
  protected readonly body = signal('');
  protected readonly busy = signal(false);
  protected readonly error = signal<ApiError | null>(null);
  protected readonly result = signal<ExplorerResult | null>(null);
  /** Commande de la requête envoyée : le formulaire peut avoir changé depuis. */
  protected readonly sentCurl = signal('');

  protected readonly hasBody = computed(() => WITH_BODY.includes(this.method()));
  protected readonly ok = computed(() => (this.result()?.status ?? 0) < 400);
  protected readonly formatted = computed(() => JSON.stringify(this.result()?.body, null, 2));

  private curl(): string {
    const data =
      this.hasBody() && this.body().trim()
        ? ` -H "Content-Type: application/json" -d '${this.body()}'`
        : '';
    return `curl -X ${this.method()} "${BASE_URL}${this.path().trim()}"${data}`;
  }

  protected use(example: Example): void {
    this.method.set(example.method);
    this.path.set(example.path);
    this.body.set(example.body ?? '');
    this.error.set(null);
    this.result.set(null);
  }

  protected send(): void {
    let body: unknown = null;
    if (this.hasBody() && this.body().trim()) {
      try {
        body = JSON.parse(this.body());
      } catch {
        this.error.set({ key: 'error_invalid_json', params: {}, field: 'body' });
        return;
      }
    }
    this.busy.set(true);
    this.error.set(null);
    this.result.set(null);
    this.sentCurl.set(this.curl());
    this.api.explore(this.method(), this.path(), body).subscribe({
      next: (result) => {
        this.busy.set(false);
        this.result.set(result);
      },
      error: (error) => {
        this.busy.set(false);
        this.error.set(toApiError(error));
      },
    });
  }
}
