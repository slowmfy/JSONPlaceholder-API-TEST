import { Component, computed, inject, input, linkedSignal, signal } from '@angular/core';

import { TranslatePipe } from '../i18n';
import { Todo } from '../models';
import { Schema } from '../schema';
import { Status, WriteStatus } from '../status';
import { ResourceList } from '../store';
import { ConfirmButton } from '../ui/confirm-button';
import { EntityForm } from '../ui/entity-form';

/** Page /todos (filtre ?userId=) ou onglet de la fiche utilisateur (`embedded`). */
@Component({
  selector: 'app-todos-list',
  imports: [TranslatePipe, Status, WriteStatus, ConfirmButton, EntityForm],
  template: `
    <section class="card">
      <div class="card-head">
        @if (embedded()) {
          <h2>{{ 'res_todos' | t }}</h2>
        } @else {
          <h1>{{ 'res_todos' | t }}</h1>
        }
        <button type="button" (click)="list.edit('new')">{{ 'action_add' | t }}</button>
      </div>

      <div class="toolbar">
        @if (!embedded()) {
          <select
            [attr.aria-label]="'field_user_id' | t"
            (change)="userFilter.set($any($event.target).value)"
          >
            <option value="">{{ 'filter_all_users' | t }}</option>
            @for (user of users(); track user.id) {
              <option [value]="user.id" [selected]="userFilter() === '' + user.id">
                {{ user.label }}
              </option>
            }
          </select>
        }
        <select
          [attr.aria-label]="'field_completed' | t"
          (change)="status.set($any($event.target).value)"
        >
          <option value="">{{ 'status_all' | t }}</option>
          <option value="true">{{ 'status_done' | t }}</option>
          <option value="false">{{ 'status_open' | t }}</option>
        </select>
        <span class="muted">{{ 'count_results' | t: { count: list.items().length } }}</span>
      </div>

      <app-status [loading]="list.source.isLoading()" [error]="list.source.error()" />
      <app-write-status [feedback]="list.feedback()" [error]="list.error()" />

      @if (list.editing() === 'new') {
        <div class="panel">
          <app-entity-form
            resource="todos"
            submitLabel="action_create"
            [fixed]="fixed()"
            [initial]="{ user_id: userFilter() }"
            [error]="list.error()"
            [busy]="list.busy()"
            (submitted)="list.save($event)"
            (cancelled)="list.edit(null)"
          />
        </div>
      }

      <ul class="rows">
        @for (todo of list.items(); track todo) {
          <li>
            @if (list.editing() === todo) {
              <div class="panel grow">
                <app-entity-form
                  resource="todos"
                  [initial]="todo"
                  [fixed]="fixed()"
                  [error]="list.error()"
                  [busy]="list.busy()"
                  (submitted)="list.save($event)"
                  (cancelled)="list.edit(null)"
                />
              </div>
            } @else {
              <label class="grow todo" [class.done]="todo.completed">
                <input
                  type="checkbox"
                  [checked]="todo.completed"
                  [disabled]="list.busy()"
                  (change)="toggle(todo, $event)"
                />
                <span class="tag">#{{ todo.id }}</span>
                <span>{{ todo.title }}</span>
              </label>
              <div class="inline">
                <button type="button" class="ghost small" (click)="list.edit(todo)">
                  {{ 'action_edit' | t }}
                </button>
                <app-confirm-button [busy]="list.busy()" (confirmed)="list.remove(todo)" />
              </div>
            }
          </li>
        } @empty {
          @if (list.source.hasValue()) {
            <li class="muted">{{ 'no_items' | t }}</li>
          }
        }
      </ul>
    </section>
  `,
})
export class TodosList {
  /** Filtre : paramètre ?userId= de la page, ou utilisateur de la fiche. */
  readonly userId = input<string | number>();
  readonly embedded = input(false);

  protected readonly users = inject(Schema).options('users');
  protected readonly userFilter = linkedSignal(() => String(this.userId() ?? ''));
  protected readonly status = signal('');
  protected readonly list = new ResourceList<Todo>('todos', () => ({
    ...(this.userFilter() ? { user_id: this.userFilter() } : {}),
    ...(this.status() ? { completed: this.status() } : {}),
  }));
  protected readonly fixed = computed(() =>
    this.embedded() ? { user_id: this.userFilter() } : {},
  );

  protected async toggle(todo: Todo, event: Event): Promise<void> {
    const box = event.target as HTMLInputElement;
    const updated = await this.list.update(todo, { completed: box.checked });
    // Après un échec, [checked] ne change pas : la case doit retrouver son état réel.
    if (!updated) {
      box.checked = todo.completed;
    }
  }
}
