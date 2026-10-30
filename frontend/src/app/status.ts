import { Component, computed, input } from '@angular/core';

import { toApiError } from './api';
import { TranslatePipe } from './i18n';
import { ApiError, Feedback } from './models';

/** Affiche « Chargement… » ou le message d'erreur traduit d'une requête. */
@Component({
  selector: 'app-status',
  imports: [TranslatePipe],
  template: `
    @if (apiError(); as e) {
      <p class="alert" role="alert">{{ e.key | t: e.params }}</p>
    } @else if (loading()) {
      <p class="muted">{{ 'loading' | t }}</p>
    }
  `,
})
export class Status {
  readonly loading = input(false);
  readonly error = input<unknown>(null);
  protected readonly apiError = computed(() => toApiError(this.error()));
}

/** Résultat d'une écriture : réussite, ou erreur qui ne concerne pas un champ de formulaire. */
@Component({
  selector: 'app-write-status',
  imports: [TranslatePipe],
  template: `
    @if (feedback(); as f) {
      <div class="success" role="status">
        <p>{{ f.key | t: f.params }}</p>
        @if (f.simulated) {
          <p class="notice">{{ 'simulated_write' | t }}</p>
        }
      </div>
    }
    @if (error(); as e) {
      @if (!e.field) {
        <p class="alert" role="alert">{{ e.key | t: e.params }}</p>
      }
    }
  `,
})
export class WriteStatus {
  readonly feedback = input<Feedback | null>(null);
  readonly error = input<ApiError | null>(null);
}
