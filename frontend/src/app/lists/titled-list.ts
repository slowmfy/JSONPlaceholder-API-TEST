import { Component, computed, inject, input, linkedSignal, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { TranslatePipe } from '../i18n';
import { Item } from '../models';
import { Schema } from '../schema';
import { Status, WriteStatus } from '../status';
import { ResourceList } from '../store';
import { ConfirmButton } from '../ui/confirm-button';
import { EntityForm } from '../ui/entity-form';

type TitledItem = Item & { title: string };

/** Liste de posts ou d'albums : pages /posts et /albums, ou onglet de la fiche utilisateur. */
@Component({
  selector: 'app-titled-list',
  imports: [RouterLink, TranslatePipe, Status, WriteStatus, ConfirmButton, EntityForm],
  template: `
    <section class="card">
      <div class="card-head">
        @if (embedded()) {
          <h2>{{ 'res_' + resource() | t }}</h2>
        } @else {
          <h1>{{ 'res_' + resource() | t }}</h1>
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
        <input
          type="search"
          [placeholder]="'field_title' | t"
          [attr.aria-label]="'field_title' | t"
          [value]="search()"
          (input)="search.set($any($event.target).value)"
        />
        <span class="muted">{{ 'count_results' | t: { count: filtered().length } }}</span>
      </div>

      <app-status [loading]="list.source.isLoading()" [error]="list.source.error()" />
      <app-write-status [feedback]="list.feedback()" [error]="list.error()" />

      @if (list.editing() === 'new') {
        <div class="panel">
          <app-entity-form
            [resource]="resource()"
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
        @for (item of filtered(); track item) {
          <li>
            @if (list.editing() === item) {
              <div class="panel grow">
                <app-entity-form
                  [resource]="resource()"
                  [initial]="item"
                  [fixed]="fixed()"
                  [error]="list.error()"
                  [busy]="list.busy()"
                  (submitted)="list.save($event)"
                  (cancelled)="list.edit(null)"
                />
              </div>
            } @else {
              <div class="grow">
                <span class="tag">#{{ item.id }}</span>
                @if (list.isLocal(item)) {
                  {{ item.title }}
                } @else {
                  <a [routerLink]="['/', resource(), item.id]">{{ item.title }}</a>
                }
              </div>
              <div class="inline">
                <button type="button" class="ghost small" (click)="list.edit(item)">
                  {{ 'action_edit' | t }}
                </button>
                <app-confirm-button [busy]="list.busy()" (confirmed)="list.remove(item)" />
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
export class TitledList {
  /** Ressource affichée ; sur les pages, elle vient de `data` dans app.routes.ts. */
  readonly resource = input.required<'posts' | 'albums'>();
  /** Filtre : paramètre ?userId= de la page, ou utilisateur de la fiche. */
  readonly userId = input<string | number>();
  readonly embedded = input(false);

  protected readonly users = inject(Schema).options('users');
  protected readonly userFilter = linkedSignal(() => String(this.userId() ?? ''));
  protected readonly search = signal('');
  protected readonly list = new ResourceList<TitledItem>(
    () => this.resource(),
    () => (this.userFilter() ? { user_id: this.userFilter() } : ({} as Record<string, string>)),
  );
  protected readonly fixed = computed(() =>
    this.embedded() ? { user_id: this.userFilter() } : {},
  );
  protected readonly filtered = computed(() => {
    const term = this.search().trim().toLowerCase();
    return this.list.items().filter((item) => item.title.toLowerCase().includes(term));
  });
}
