import { Component, computed, input } from '@angular/core';

import { TranslatePipe } from '../i18n';
import { Photo } from '../models';
import { Status, WriteStatus } from '../status';
import { ResourceList } from '../store';
import { ConfirmButton } from '../ui/confirm-button';
import { EntityForm } from '../ui/entity-form';

/** Photos d'un album, sur la page de détail de l'album. */
@Component({
  selector: 'app-photos-grid',
  imports: [TranslatePipe, Status, WriteStatus, ConfirmButton, EntityForm],
  template: `
    <section class="card">
      <div class="card-head">
        <h2>{{ 'res_photos' | t }}</h2>
        <button type="button" (click)="list.edit('new')">{{ 'action_add' | t }}</button>
      </div>

      <app-status [loading]="list.source.isLoading()" [error]="list.source.error()" />
      <app-write-status [feedback]="list.feedback()" [error]="list.error()" />

      @if (list.editing() === 'new') {
        <div class="panel">
          <app-entity-form
            resource="photos"
            submitLabel="action_create"
            [fixed]="fixed()"
            [error]="list.error()"
            [busy]="list.busy()"
            (submitted)="list.save($event)"
            (cancelled)="list.edit(null)"
          />
        </div>
      }

      <ul class="photos">
        @for (photo of list.items(); track photo) {
          <li [class.wide]="list.editing() === photo">
            @if (list.editing() === photo) {
              <div class="panel">
                <app-entity-form
                  resource="photos"
                  [initial]="photo"
                  [fixed]="fixed()"
                  [error]="list.error()"
                  [busy]="list.busy()"
                  (submitted)="list.save($event)"
                  (cancelled)="list.edit(null)"
                />
              </div>
            } @else {
              <a [href]="photo.url" target="_blank" rel="noopener">
                <img [src]="photo.thumbnail_url" [alt]="photo.title" loading="lazy" />
              </a>
              <p class="photo-title" [title]="photo.title">
                <span class="tag">#{{ photo.id }}</span> {{ photo.title }}
              </p>
              <div class="inline">
                <button type="button" class="ghost small" (click)="list.edit(photo)">
                  {{ 'action_edit' | t }}
                </button>
                <app-confirm-button [busy]="list.busy()" (confirmed)="list.remove(photo)" />
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
export class PhotosGrid {
  readonly albumId = input.required<string | number>();

  protected readonly list = new ResourceList<Photo>('photos', () => ({ album_id: this.albumId() }));
  protected readonly fixed = computed(() => ({ album_id: this.albumId() }));
}
