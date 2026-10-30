import { Component, computed, input } from '@angular/core';

import { TranslatePipe } from '../i18n';
import { Comment } from '../models';
import { Status, WriteStatus } from '../status';
import { ResourceList } from '../store';
import { ConfirmButton } from '../ui/confirm-button';
import { EntityForm } from '../ui/entity-form';

/** Commentaires d'un post, sur la page de détail du post. */
@Component({
  selector: 'app-comments-list',
  imports: [TranslatePipe, Status, WriteStatus, ConfirmButton, EntityForm],
  template: `
    <section class="card">
      <div class="card-head">
        <h2>{{ 'res_comments' | t }}</h2>
        <button type="button" (click)="list.edit('new')">{{ 'action_add' | t }}</button>
      </div>

      <app-status [loading]="list.source.isLoading()" [error]="list.source.error()" />
      <app-write-status [feedback]="list.feedback()" [error]="list.error()" />

      @if (list.editing() === 'new') {
        <div class="panel">
          <app-entity-form
            resource="comments"
            submitLabel="action_create"
            [fixed]="fixed()"
            [error]="list.error()"
            [busy]="list.busy()"
            (submitted)="list.save($event)"
            (cancelled)="list.edit(null)"
          />
        </div>
      }

      <ul class="comments">
        @for (comment of list.items(); track comment) {
          <li>
            @if (list.editing() === comment) {
              <div class="panel">
                <app-entity-form
                  resource="comments"
                  [initial]="comment"
                  [fixed]="fixed()"
                  [error]="list.error()"
                  [busy]="list.busy()"
                  (submitted)="list.save($event)"
                  (cancelled)="list.edit(null)"
                />
              </div>
            } @else {
              <p class="comment-head">
                <strong>{{ comment.name }}</strong>
                <span class="muted">{{ comment.email }}</span>
              </p>
              <p>{{ comment.body }}</p>
              <div class="inline">
                <button type="button" class="ghost small" (click)="list.edit(comment)">
                  {{ 'action_edit' | t }}
                </button>
                <app-confirm-button [busy]="list.busy()" (confirmed)="list.remove(comment)" />
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
export class CommentsList {
  readonly postId = input.required<string | number>();

  protected readonly list = new ResourceList<Comment>('comments', () => ({
    post_id: this.postId(),
  }));
  protected readonly fixed = computed(() => ({ post_id: this.postId() }));
}
