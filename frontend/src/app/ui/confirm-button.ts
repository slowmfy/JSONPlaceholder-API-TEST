import { Component, input, output, signal } from '@angular/core';

import { TranslatePipe } from '../i18n';

/** Bouton « Supprimer » qui demande une confirmation sur place. */
@Component({
  selector: 'app-confirm-button',
  imports: [TranslatePipe],
  template: `
    @if (asking()) {
      <span class="confirm-inline" role="group">
        <span>{{ 'confirm_delete' | t }}</span>
        <button type="button" class="danger small" [disabled]="busy()" (click)="confirm()">
          {{ 'action_delete' | t }}
        </button>
        <button type="button" class="ghost small" (click)="asking.set(false)">
          {{ 'action_cancel' | t }}
        </button>
      </span>
    } @else {
      <button type="button" class="danger ghost small" (click)="asking.set(true)">
        {{ 'action_delete' | t }}
      </button>
    }
  `,
})
export class ConfirmButton {
  readonly busy = input(false);
  readonly confirmed = output<void>();
  protected readonly asking = signal(false);

  protected confirm(): void {
    this.asking.set(false);
    this.confirmed.emit();
  }
}
