import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { TranslatePipe } from '../i18n';
import { PhotosGrid } from '../lists/photos-grid';
import { Album, User } from '../models';
import { Status, WriteStatus } from '../status';
import { ResourceItem } from '../store';
import { ConfirmButton } from '../ui/confirm-button';
import { EntityForm } from '../ui/entity-form';

@Component({
  selector: 'app-album-detail-page',
  imports: [RouterLink, TranslatePipe, Status, WriteStatus, ConfirmButton, EntityForm, PhotosGrid],
  template: `
    @if (owner.value(); as o) {
      <a [routerLink]="['/users', o.id]" class="back">← {{ o.name }}</a>
    } @else {
      <a routerLink="/albums" class="back">← {{ 'nav_albums' | t }}</a>
    }

    <app-status [loading]="album.source.isLoading()" [error]="album.source.error()" />
    <app-write-status [feedback]="album.feedback()" [error]="album.error()" />

    @if (album.exists()) {
      @let a = album.value()!;
      <section class="card">
        @if (album.editing()) {
          <app-entity-form
            resource="albums"
            [initial]="a"
            [error]="album.error()"
            [busy]="album.busy()"
            (submitted)="album.save($event)"
            (cancelled)="album.edit(false)"
          />
        } @else {
          <div class="card-head">
            <div>
              <span class="tag">#{{ a.id }}</span>
              <h1>{{ a.title }}</h1>
              @if (owner.value(); as o) {
                <p class="muted">{{ 'post_by' | t: { name: o.name } }}</p>
              }
            </div>
            <div class="inline">
              <button type="button" class="ghost small" (click)="album.edit(true)">
                {{ 'action_edit' | t }}
              </button>
              <app-confirm-button [busy]="album.busy()" (confirmed)="album.remove()" />
            </div>
          </div>
        }
      </section>

      <app-photos-grid [albumId]="id()" />
    }
  `,
})
export class AlbumDetailPage {
  /** Paramètre :id de l'URL. */
  readonly id = input.required<string>();

  protected readonly album = new ResourceItem<Album>('albums', () => this.id());
  protected readonly owner = new ResourceItem<User>('users', () => this.album.value()?.user_id);
}
