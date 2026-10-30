import { Component, computed, inject, input, linkedSignal, output } from '@angular/core';

import { TranslatePipe } from '../i18n';
import { ApiError, FieldDef } from '../models';
import { Schema } from '../schema';

let nextFormId = 0;

/**
 * Formulaire de création ou de modification, généré à partir de la description
 * de la ressource. Les contrôles sont faits par l'API (validators.py) : les
 * erreurs reviennent avec le nom du champ et s'affichent sous celui-ci.
 */
@Component({
  selector: 'app-entity-form',
  imports: [TranslatePipe],
  template: `
    <form class="form" novalidate (submit)="$event.preventDefault(); submit()">
      @for (field of fields(); track field.name) {
        <div class="field" [class.checkbox]="field.kind === 'bool'">
          <label [for]="uid + field.name">
            {{ 'field_' + field.name | t }}
            @if (!field.required && field.kind !== 'bool') {
              <span class="muted">({{ 'optional' | t }})</span>
            }
          </label>
          @switch (field.kind) {
            @case ('textarea') {
              <textarea
                [id]="uid + field.name"
                rows="4"
                [value]="text(field)"
                [class.invalid]="errorOf(field)"
                [attr.aria-invalid]="errorOf(field) ? 'true' : null"
                (input)="set(field, $any($event.target).value)"
              ></textarea>
            }
            @case ('bool') {
              <input
                type="checkbox"
                [id]="uid + field.name"
                [checked]="!!values()[field.name]"
                (change)="set(field, $any($event.target).checked)"
              />
            }
            @case ('ref') {
              <select
                [id]="uid + field.name"
                [class.invalid]="errorOf(field)"
                [attr.aria-invalid]="errorOf(field) ? 'true' : null"
                (change)="set(field, $any($event.target).value)"
              >
                <option value="">{{ 'select_placeholder' | t }}</option>
                @for (option of schema.options(field.ref!)(); track option.id) {
                  <option [value]="option.id" [selected]="text(field) === '' + option.id">
                    {{ option.id }} — {{ option.label }}
                  </option>
                }
              </select>
            }
            @default {
              <input
                [type]="field.kind === 'text' ? 'text' : field.kind"
                [id]="uid + field.name"
                [value]="text(field)"
                [class.invalid]="errorOf(field)"
                [attr.aria-invalid]="errorOf(field) ? 'true' : null"
                [placeholder]="field.kind === 'email' ? ('email_example' | t) : ''"
                (input)="set(field, $any($event.target).value)"
              />
            }
          }
          @if (errorOf(field); as e) {
            <p class="field-error">{{ e.key | t: e.params }}</p>
          }
        </div>
      }
      <div class="inline">
        <button type="submit" [disabled]="busy()">{{ submitLabel() | t }}</button>
        <button type="button" class="ghost" (click)="cancelled.emit()">
          {{ 'action_cancel' | t }}
        </button>
      </div>
    </form>
  `,
})
export class EntityForm {
  protected readonly schema = inject(Schema);

  readonly resource = input.required<string>();
  /** Valeurs de départ : l'élément modifié, ou des valeurs proposées. */
  readonly initial = input<object | null>(null);
  /** Champs imposés par le contexte et masqués (ex. post_id d'un commentaire). */
  readonly fixed = input<Record<string, unknown>>({});
  readonly error = input<ApiError | null>(null);
  readonly busy = input(false);
  readonly submitLabel = input('action_save');
  readonly submitted = output<Record<string, unknown>>();
  readonly cancelled = output<void>();

  protected readonly uid = `form-${nextFormId++}-`;
  protected readonly fields = computed(() =>
    this.schema.fields(this.resource()).filter((field) => !(field.name in this.fixed())),
  );
  protected readonly values = linkedSignal<Record<string, unknown>>(() => ({
    ...(this.initial() ?? {}),
  }));

  protected text(field: FieldDef): string {
    return String(this.values()[field.name] ?? '');
  }

  protected set(field: FieldDef, value: unknown): void {
    this.values.update((values) => ({ ...values, [field.name]: value }));
  }

  protected errorOf(field: FieldDef): ApiError | null {
    const error = this.error();
    return error?.field === field.name ? error : null;
  }

  protected submit(): void {
    const values: Record<string, unknown> = { ...this.fixed() };
    for (const field of this.fields()) {
      values[field.name] = this.values()[field.name] ?? (field.kind === 'bool' ? false : '');
    }
    this.submitted.emit(values);
  }
}
